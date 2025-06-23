import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
import redis.asyncio as redis

from ..models import Country, EconomicIndicator
from ..core.logging import get_logger

logger = get_logger(__name__)

class WorldBankService:
    """
    World Bank API integration for governance and economic indicators
    Following technical specification for governance quality metrics
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.base_url = "https://api.worldbank.org/v2"
        self.redis_client = redis_client
        self.rate_limit_delay = 8.64  # seconds between requests per spec
        
        # Key governance indicators from technical spec
        self.governance_indicators = {
            "PV.EST": "Political Stability",
            "GE.EST": "Government Effectiveness", 
            "RQ.EST": "Regulatory Quality",
            "RL.EST": "Rule of Law",
            "CC.EST": "Control of Corruption"
        }
        
        # Additional economic indicators
        self.economic_indicators = {
            "NY.GDP.MKTP.KD.ZG": "GDP Growth",
            "FP.CPI.TOTL.ZG": "Inflation",
            "GC.DOD.TOTL.GD.ZS": "Debt to GDP",
            "NE.TRD.GNFS.ZS": "Trade (% of GDP)"
        }
        
        self.all_indicators = {**self.governance_indicators, **self.economic_indicators}
    
    async def collect_country_indicators(
        self, 
        session: AsyncSession,
        country_iso: str,
        start_year: int = 2020,
        end_year: int = 2024
    ) -> Dict[str, Any]:
        """
        Collect all indicators for a specific country
        
        Args:
            session: Database session
            country_iso: ISO 3-letter country code
            start_year: Starting year for data collection
            end_year: Ending year for data collection
            
        Returns:
            Dictionary of indicator values by year
        """
        country_data = {}
        
        for indicator_code, indicator_name in self.all_indicators.items():
            try:
                await self._enforce_rate_limit(f"wb_{indicator_code}_{country_iso}")
                
                indicator_data = await self._fetch_indicator(
                    country_iso, indicator_code, start_year, end_year
                )
                
                if indicator_data:
                    # Store in database
                    await self._store_indicator_data(
                        session, country_iso, indicator_code, indicator_data
                    )
                    country_data[indicator_code] = indicator_data
                    
            except Exception as e:
                logger.error(f"Error collecting {indicator_name} for {country_iso}: {str(e)}")
                continue
                
        return country_data
    
    async def collect_all_countries_indicators(self, session: AsyncSession) -> Dict[str, Dict]:
        """
        Collect indicators for all countries in database
        
        Returns:
            Dictionary mapping country codes to their indicator data
        """
        # Get all countries
        result = await session.execute(
            select(Country.code, Country.name).where(Country.code.isnot(None))
        )
        countries = result.fetchall()
        
        all_data = {}
        
        for country_code, country_name in countries:
            try:
                logger.info(f"Collecting World Bank data for {country_name} ({country_code})")
                
                indicators = await self.collect_country_indicators(session, country_code)
                all_data[country_code] = indicators
                
                # Brief delay between countries
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to collect indicators for {country_name}: {str(e)}")
                all_data[country_code] = {}
                
        return all_data
    
    async def _fetch_indicator(
        self, 
        country_iso: str, 
        indicator_code: str,
        start_year: int,
        end_year: int
    ) -> List[Dict[str, Any]]:
        """Fetch a specific indicator from World Bank API"""
        try:
            url = f"{self.base_url}/country/{country_iso}/indicator/{indicator_code}"
            params = {
                "format": "json",
                "date": f"{start_year}:{end_year}",
                "per_page": 500
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # World Bank API returns array with metadata as first element
                        if isinstance(data, list) and len(data) > 1:
                            indicator_data = []
                            for record in data[1]:  # Skip metadata
                                if record.get("value") is not None:
                                    indicator_data.append({
                                        "year": int(record["date"]),
                                        "value": float(record["value"]),
                                        "country": record["country"]["value"],
                                        "indicator": record["indicator"]["value"]
                                    })
                            
                            return sorted(indicator_data, key=lambda x: x["year"])
                        
                    elif response.status == 404:
                        logger.warning(f"Indicator {indicator_code} not found for {country_iso}")
                    else:
                        logger.error(f"World Bank API error: {response.status}")
                        
                    return []
                    
        except asyncio.TimeoutError:
            logger.error(f"World Bank API timeout for {country_iso}/{indicator_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {indicator_code} for {country_iso}: {str(e)}")
            return []
    
    async def _store_indicator_data(
        self,
        session: AsyncSession,
        country_iso: str,
        indicator_code: str,
        indicator_data: List[Dict[str, Any]]
    ) -> None:
        """Store indicator data in database"""
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
            
            # Prepare records for bulk insert/update
            for record in indicator_data:
                try:
                    # Check if record exists
                    existing = await session.execute(
                        select(EconomicIndicator.id).where(
                            EconomicIndicator.country_id == country_id,
                            EconomicIndicator.indicator_code == indicator_code,
                            EconomicIndicator.year == record["year"]
                        )
                    )
                    
                    if existing.fetchone():
                        # Update existing record
                        await session.execute(
                            update(EconomicIndicator)
                            .where(
                                EconomicIndicator.country_id == country_id,
                                EconomicIndicator.indicator_code == indicator_code,
                                EconomicIndicator.year == record["year"]
                            )
                            .values(value=record["value"])
                        )
                    else:
                        # Insert new record
                        await session.execute(
                            insert(EconomicIndicator).values(
                                country_id=country_id,
                                indicator_code=indicator_code,
                                year=record["year"],
                                value=record["value"]
                            )
                        )
                        
                except Exception as e:
                    logger.warning(f"Error storing indicator record: {str(e)}")
                    continue
            
            await session.commit()
            logger.info(f"Stored {len(indicator_data)} {indicator_code} records for {country_iso}")
            
        except Exception as e:
            logger.error(f"Error storing indicator data: {str(e)}")
            await session.rollback()
    
    async def _enforce_rate_limit(self, key_suffix: str) -> None:
        """Enforce World Bank API rate limiting"""
        try:
            rate_key = f"wb_api_calls_{key_suffix}"
            last_call = await self.redis_client.get(rate_key)
            
            if last_call:
                last_call_time = float(last_call)
                time_since_last = datetime.now().timestamp() - last_call_time
                
                if time_since_last < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)
            
            await self.redis_client.set(
                rate_key,
                datetime.now().timestamp(),
                ex=3600
            )
            
        except Exception as e:
            logger.warning(f"Rate limiting error: {str(e)}")
            await asyncio.sleep(self.rate_limit_delay)
    
    async def get_latest_indicators(
        self,
        session: AsyncSession,
        country_iso: str
    ) -> Dict[str, Any]:
        """
        Get the most recent indicator values for a country
        
        Returns:
            Dictionary of latest indicator values
        """
        try:
            result = await session.execute(
                select(Country.id).where(Country.code == country_iso)
            )
            country_row = result.fetchone()
            if not country_row:
                return {}
                
            country_id = country_row[0]
            
            # Get latest value for each indicator
            latest_indicators = {}
            
            for indicator_code, indicator_name in self.all_indicators.items():
                result = await session.execute(
                    select(EconomicIndicator.year, EconomicIndicator.value)
                    .where(
                        EconomicIndicator.country_id == country_id,
                        EconomicIndicator.indicator_code == indicator_code
                    )
                    .order_by(EconomicIndicator.year.desc())
                    .limit(1)
                )
                
                latest = result.fetchone()
                if latest:
                    latest_indicators[indicator_code] = {
                        "value": float(latest.value),
                        "year": latest.year,
                        "name": indicator_name
                    }
            
            return latest_indicators
            
        except Exception as e:
            logger.error(f"Error getting latest indicators for {country_iso}: {str(e)}")
            return {}
    
    async def get_governance_score(
        self,
        session: AsyncSession, 
        country_iso: str
    ) -> Optional[float]:
        """
        Calculate composite governance score from World Bank indicators
        
        Returns:
            Composite governance score (0-100 scale)
        """
        try:
            indicators = await self.get_latest_indicators(session, country_iso)
            
            governance_values = []
            for code in self.governance_indicators.keys():
                if code in indicators:
                    # World Bank governance indicators range from -2.5 to 2.5
                    # Convert to 0-100 scale
                    raw_value = indicators[code]["value"]
                    scaled_value = ((raw_value + 2.5) / 5.0) * 100
                    governance_values.append(max(0, min(100, scaled_value)))
            
            if governance_values:
                return sum(governance_values) / len(governance_values)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating governance score for {country_iso}: {str(e)}")
            return None