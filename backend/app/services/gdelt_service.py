import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
import redis.asyncio as redis
from urllib.parse import quote

from ..models import Country, RawEvent
from ..core.logging import get_logger

logger = get_logger(__name__)

class GDELTService:
    """
    GDELT API integration service for real-time event collection
    Following technical specification rate limits and data structure
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        self.redis_client = redis_client
        self.rate_limit_key = "gdelt_api_calls"
        self.rate_limit_delay = 86.4  # seconds between requests per spec
        
    async def collect_country_events(
        self, 
        session: AsyncSession,
        country_iso: str,
        days_back: int = 7,
        max_records: int = 250
    ) -> List[Dict[str, Any]]:
        """
        Collect events for a specific country from GDELT API
        
        Args:
            session: Database session
            country_iso: ISO 3-letter country code
            days_back: Number of days to look back
            max_records: Maximum records per request
            
        Returns:
            List of event dictionaries
        """
        try:
            # Check rate limiting
            await self._enforce_rate_limit()
            
            # Build query parameters
            query = f"country:{country_iso} sourcelang:eng"
            params = {
                "query": query,
                "mode": "artlist",
                "timespan": f"{days_back}d",
                "maxrecords": max_records,
                "format": "json"
            }
            
            logger.info(f"Collecting GDELT events for {country_iso} ({days_back} days)")
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        
                        # Store raw events in database
                        await self._store_raw_events(session, country_iso, articles)
                        
                        logger.info(f"Collected {len(articles)} events for {country_iso}")
                        return articles
                    else:
                        logger.error(f"GDELT API error for {country_iso}: {response.status}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.error(f"GDELT API timeout for {country_iso}")
            return []
        except Exception as e:
            logger.error(f"Error collecting GDELT events for {country_iso}: {str(e)}")
            return []
    
    async def collect_all_countries_events(self, session: AsyncSession) -> Dict[str, List[Dict]]:
        """
        Collect events for all countries in database
        
        Returns:
            Dictionary mapping country ISO codes to event lists
        """
        # Get all country ISO codes from database
        result = await session.execute(
            select(Country.code, Country.name).where(Country.code.isnot(None))
        )
        countries = result.fetchall()
        
        all_events = {}
        
        for country_code, country_name in countries:
            try:
                events = await self.collect_country_events(session, country_code)
                all_events[country_code] = events
                
                # Rate limiting delay between countries
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Failed to collect events for {country_name} ({country_code}): {str(e)}")
                all_events[country_code] = []
                
        return all_events
    
    async def _store_raw_events(
        self, 
        session: AsyncSession, 
        country_iso: str, 
        articles: List[Dict[str, Any]]
    ) -> None:
        """Store raw events in database"""
        try:
            # Get country ID
            result = await session.execute(
                select(Country.id).where(Country.code == country_iso)
            )
            country_row = result.fetchone()
            if not country_row:
                logger.warning(f"Country not found: {country_iso}")
                return
                
            country_id = country_row[0]
            
            # Prepare event records
            events_to_insert = []
            for article in articles:
                try:
                    # Parse event date from seendate
                    seen_date = article.get("seendate", "")
                    if seen_date:
                        # GDELT seendate format: "20240115T123000Z"
                        event_date = datetime.strptime(seen_date[:8], "%Y%m%d").date()
                    else:
                        event_date = datetime.now().date()
                    
                    event_record = {
                        "country_id": country_id,
                        "event_date": event_date,
                        "title": article.get("title", "")[:1000],  # Truncate long titles
                        "source_url": article.get("url", "")[:500],
                        "domain": article.get("domain", "")[:100],
                        "language": article.get("language", "eng")[:10],
                        "tone": None  # Will be calculated during processing
                    }
                    events_to_insert.append(event_record)
                    
                except Exception as e:
                    logger.warning(f"Error parsing article: {str(e)}")
                    continue
            
            if events_to_insert:
                # Bulk insert events
                await session.execute(insert(RawEvent), events_to_insert)
                await session.commit()
                logger.info(f"Stored {len(events_to_insert)} raw events for {country_iso}")
                
        except Exception as e:
            logger.error(f"Error storing raw events for {country_iso}: {str(e)}")
            await session.rollback()
    
    async def _enforce_rate_limit(self) -> None:
        """Enforce GDELT API rate limiting using Redis"""
        try:
            # Get last API call timestamp
            last_call = await self.redis_client.get(self.rate_limit_key)
            
            if last_call:
                last_call_time = float(last_call)
                time_since_last = datetime.now().timestamp() - last_call_time
                
                if time_since_last < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    logger.info(f"Rate limiting: sleeping {sleep_time:.1f} seconds")
                    await asyncio.sleep(sleep_time)
            
            # Update last call timestamp
            await self.redis_client.set(
                self.rate_limit_key, 
                datetime.now().timestamp(),
                ex=3600  # Expire after 1 hour
            )
            
        except Exception as e:
            logger.warning(f"Rate limiting error: {str(e)}")
            # Fallback to simple delay
            await asyncio.sleep(self.rate_limit_delay)
    
    async def get_recent_events(
        self, 
        session: AsyncSession, 
        country_iso: str, 
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get recent events for a country from database
        
        Args:
            session: Database session
            country_iso: ISO country code
            days: Number of days back to query
            
        Returns:
            List of recent events
        """
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days)
            
            result = await session.execute(
                select(RawEvent, Country.name)
                .join(Country)
                .where(
                    Country.code == country_iso,
                    RawEvent.event_date >= cutoff_date
                )
                .order_by(RawEvent.event_date.desc())
                .limit(100)
            )
            
            events = []
            for raw_event, country_name in result.fetchall():
                events.append({
                    "date": raw_event.event_date.isoformat(),
                    "title": raw_event.title,
                    "source_url": raw_event.source_url,
                    "domain": raw_event.domain,
                    "language": raw_event.language
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent events for {country_iso}: {str(e)}")
            return []