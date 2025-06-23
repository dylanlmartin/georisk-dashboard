import re
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from textblob import TextBlob
from datetime import datetime

from ..models import RawEvent, ProcessedEvent
from ..core.logging import get_logger

logger = get_logger(__name__)

class EventProcessingService:
    """
    Event processing service implementing NLP pipeline from technical specification
    Uses TextBlob for sentiment analysis and regex patterns for event classification
    """
    
    def __init__(self):
        # Event classification patterns from technical spec
        self.classification_patterns = {
            'conflict': re.compile(
                r'\b(attack|violence|fight|battle|war|conflict|assault|military|bombing|terrorism|insurgency)\b',
                re.IGNORECASE
            ),
            'protest': re.compile(
                r'\b(protest|demonstration|rally|march|strike|riot|unrest|civil)\b',
                re.IGNORECASE
            ),
            'diplomatic': re.compile(
                r'\b(meeting|summit|negotiation|treaty|agreement|talks|diplomatic|embassy|ambassador)\b',
                re.IGNORECASE
            ),
            'economic': re.compile(
                r'\b(trade|economic|sanctions|embargo|tariff|commerce|inflation|gdp|financial|market)\b',
                re.IGNORECASE
            )
        }
        
        # Conflict keywords for severity weighting
        self.conflict_keywords = [
            'attack', 'violence', 'fight', 'battle', 'war', 'conflict', 
            'assault', 'military', 'bombing', 'terrorism', 'insurgency'
        ]
        
    async def process_raw_events(
        self, 
        session: AsyncSession,
        country_id: Optional[int] = None,
        batch_size: int = 100
    ) -> int:
        """
        Process raw events through NLP pipeline
        
        Args:
            session: Database session
            country_id: Optional country filter
            batch_size: Number of events to process at once
            
        Returns:
            Number of events processed
        """
        processed_count = 0
        
        try:
            # Get unprocessed raw events
            query = select(RawEvent).outerjoin(ProcessedEvent).where(
                ProcessedEvent.id.is_(None)  # No corresponding processed event
            )
            
            if country_id:
                query = query.where(RawEvent.country_id == country_id)
                
            result = await session.execute(query.limit(batch_size))
            raw_events = result.scalars().all()
            
            if not raw_events:
                logger.info("No unprocessed events found")
                return 0
            
            logger.info(f"Processing {len(raw_events)} raw events")
            
            # Process events in parallel batches
            batch_tasks = []
            for event in raw_events:
                batch_tasks.append(self._process_single_event(session, event))
                
                # Process in smaller batches to avoid overwhelming the session
                if len(batch_tasks) >= 10:
                    await asyncio.gather(*batch_tasks)
                    processed_count += len(batch_tasks)
                    batch_tasks = []
            
            # Process remaining events
            if batch_tasks:
                await asyncio.gather(*batch_tasks)
                processed_count += len(batch_tasks)
            
            await session.commit()
            logger.info(f"Successfully processed {processed_count} events")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing raw events: {str(e)}")
            await session.rollback()
            return processed_count
    
    async def _process_single_event(
        self, 
        session: AsyncSession, 
        raw_event: RawEvent
    ) -> None:
        """Process a single raw event through NLP pipeline"""
        try:
            title = raw_event.title or ""
            if not title.strip():
                return
            
            # 1. Event Classification
            risk_category = self._classify_event(title)
            
            # 2. Sentiment Analysis
            sentiment_score = self._analyze_sentiment(title)
            
            # 3. Severity Scoring
            severity_score = self._calculate_severity(title, sentiment_score)
            
            # 4. Confidence Calculation
            confidence = self._calculate_confidence(title, risk_category)
            
            # Store processed event
            processed_event = {
                "raw_event_id": raw_event.id,
                "risk_category": risk_category,
                "sentiment_score": round(sentiment_score, 2),
                "severity_score": round(severity_score, 2),
                "confidence": round(confidence, 2)
            }
            
            await session.execute(insert(ProcessedEvent).values(**processed_event))
            
        except Exception as e:
            logger.warning(f"Error processing event {raw_event.id}: {str(e)}")
    
    def _classify_event(self, title: str) -> str:
        """
        Classify event using regex patterns from technical specification
        
        Returns:
            Event category: conflict, protest, diplomatic, economic, or other
        """
        title_lower = title.lower()
        
        # Check each category pattern
        for category, pattern in self.classification_patterns.items():
            if pattern.search(title):
                return category
        
        return 'other'
    
    def _analyze_sentiment(self, title: str) -> float:
        """
        Analyze sentiment using TextBlob
        
        Returns:
            Sentiment score from -1 (negative) to 1 (positive)
        """
        try:
            blob = TextBlob(title)
            # TextBlob polarity ranges from -1 to 1
            return blob.sentiment.polarity
        except Exception as e:
            logger.warning(f"Error analyzing sentiment for '{title}': {str(e)}")
            return 0.0
    
    def _calculate_severity(self, title: str, sentiment_score: float) -> float:
        """
        Calculate severity score using algorithm from technical specification
        
        Algorithm:
        - Base severity: 0.5
        - Adjust for negative sentiment: severity += abs(min(0, sentiment_score)) * 0.3
        - Adjust for conflict keywords: severity += conflict_keyword_count * 0.1
        - Clamp to [0, 1] range
        
        Returns:
            Severity score from 0 to 1
        """
        base_severity = 0.5
        
        # Adjust for negative sentiment
        negative_sentiment_boost = abs(min(0, sentiment_score)) * 0.3
        
        # Count conflict keywords
        title_lower = title.lower()
        conflict_count = sum(1 for keyword in self.conflict_keywords if keyword in title_lower)
        conflict_boost = conflict_count * 0.1
        
        severity = base_severity + negative_sentiment_boost + conflict_boost
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, severity))
    
    def _calculate_confidence(self, title: str, risk_category: str) -> float:
        """
        Calculate confidence in classification and scoring
        
        Returns:
            Confidence score from 0 to 1
        """
        base_confidence = 0.7
        
        # Higher confidence for longer, more descriptive titles
        length_factor = min(0.2, len(title.split()) / 50)  # Up to 0.2 boost for long titles
        
        # Higher confidence for clear category matches
        category_factor = 0.1 if risk_category != 'other' else 0.0
        
        # Lower confidence for very short titles
        if len(title) < 20:
            length_penalty = -0.2
        else:
            length_penalty = 0.0
        
        confidence = base_confidence + length_factor + category_factor + length_penalty
        
        return max(0.1, min(1.0, confidence))
    
    async def get_processed_events_summary(
        self,
        session: AsyncSession,
        country_id: int,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get summary of processed events for a country
        
        Returns:
            Dictionary with event counts, sentiment averages, etc.
        """
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now().date() - timedelta(days=days_back)
            
            # Get processed events joined with raw events
            result = await session.execute(
                select(ProcessedEvent, RawEvent)
                .join(RawEvent)
                .where(
                    RawEvent.country_id == country_id,
                    RawEvent.event_date >= cutoff_date
                )
            )
            
            events = result.fetchall()
            
            if not events:
                return {
                    "total_events": 0,
                    "categories": {},
                    "avg_sentiment": 0,
                    "avg_severity": 0,
                    "confidence": 0
                }
            
            # Calculate summary statistics
            categories = {}
            sentiments = []
            severities = []
            confidences = []
            
            for processed_event, raw_event in events:
                # Count by category
                category = processed_event.risk_category
                categories[category] = categories.get(category, 0) + 1
                
                # Collect metrics
                if processed_event.sentiment_score is not None:
                    sentiments.append(float(processed_event.sentiment_score))
                if processed_event.severity_score is not None:
                    severities.append(float(processed_event.severity_score))
                if processed_event.confidence is not None:
                    confidences.append(float(processed_event.confidence))
            
            return {
                "total_events": len(events),
                "categories": categories,
                "avg_sentiment": sum(sentiments) / len(sentiments) if sentiments else 0,
                "avg_severity": sum(severities) / len(severities) if severities else 0,
                "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                "period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Error getting events summary for country {country_id}: {str(e)}")
            return {
                "total_events": 0,
                "categories": {},
                "avg_sentiment": 0,
                "avg_severity": 0,
                "confidence": 0
            }