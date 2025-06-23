import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import SessionLocal
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.news_event import NewsEvent
from app.core.data_collector import DataCollector
from app.core.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

class RiskService:
    def __init__(self):
        self.data_collector = DataCollector()
        self.risk_engine = RiskEngine()
    
    async def update_country_risk_scores(self, country_codes: List[str] = None) -> Dict[str, Any]:
        """Update risk scores for specified countries or all countries"""
        db = SessionLocal()
        results = {
            'updated_countries': 0,
            'errors': [],
            'news_articles_collected': 0,
            'economic_data_points': 0
        }
        
        try:
            # Get countries to update
            if country_codes:
                countries = db.query(Country).filter(Country.code.in_(country_codes)).all()
            else:
                countries = db.query(Country).all()
            
            logger.info(f"Starting risk score update for {len(countries)} countries")
            
            for country in countries:
                try:
                    await self._update_single_country(db, country, results)
                    results['updated_countries'] += 1
                    
                    # Small delay to be respectful to APIs
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error updating {country.name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
            
            db.commit()
            logger.info(f"Risk score update completed. Updated {results['updated_countries']} countries")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Risk score update failed: {e}")
            results['errors'].append(f"Update failed: {str(e)}")
        finally:
            db.close()
        
        return results
    
    async def _update_single_country(self, db: Session, country: Country, results: Dict[str, Any]):
        """Update risk scores for a single country"""
        logger.info(f"Updating risk scores for {country.name}")
        
        # Collect data
        country_data = await self.data_collector.collect_country_data(
            country.name, country.code
        )
        
        news_articles = country_data['news_articles']
        economic_data = country_data['economic_data']
        
        results['news_articles_collected'] += len(news_articles)
        results['economic_data_points'] += sum(1 for v in economic_data.values() if v is not None)
        
        # Store news events in database
        for article_data in news_articles:
            # Calculate sentiment for this article
            sentiment = self.risk_engine.sentiment_analyzer.polarity_scores(
                article_data['headline']
            )
            
            news_event = NewsEvent(
                country_code=country.code,
                headline=article_data['headline'],
                source=article_data['source'],
                sentiment_score=sentiment['compound'],
                published_at=article_data['published_at'],
                processed_at=datetime.utcnow()
            )
            db.add(news_event)
        
        # Calculate risk scores
        risk_scores = self.risk_engine.calculate_risk_scores(news_articles, economic_data, country.code)
        
        # Store risk score in database (convert numpy types to Python types)
        risk_score = RiskScore(
            country_code=country.code,
            timestamp=datetime.utcnow(),
            overall_score=float(risk_scores.overall),
            political_score=float(risk_scores.political),
            economic_score=float(risk_scores.economic),
            security_score=float(risk_scores.security),
            social_score=float(risk_scores.social),
            confidence_level=float(risk_scores.confidence)
        )
        db.add(risk_score)
        
        logger.info(f"Updated {country.name}: Overall Risk {risk_scores.overall:.1f}, "
                   f"Political {risk_scores.political:.1f}, Economic {risk_scores.economic:.1f}, "
                   f"Security {risk_scores.security:.1f}, Social {risk_scores.social:.1f}")
    
    async def collect_sample_data_for_country(self, country_name: str, country_code: str) -> Dict[str, Any]:
        """Collect and analyze data for a single country (for testing)"""
        try:
            country_data = await self.data_collector.collect_country_data(country_name, country_code)
            risk_scores = self.risk_engine.calculate_risk_scores(
                country_data['news_articles'], 
                country_data['economic_data'],
                country_code
            )
            
            return {
                'country': {'name': country_name, 'code': country_code},
                'news_articles': len(country_data['news_articles']),
                'economic_data': country_data['economic_data'],
                'risk_scores': {
                    'overall': risk_scores.overall,
                    'political': risk_scores.political,
                    'economic': risk_scores.economic,
                    'security': risk_scores.security,
                    'social': risk_scores.social,
                    'confidence': risk_scores.confidence
                },
                'sample_headlines': [
                    article['headline'] for article in country_data['news_articles'][:3]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error collecting sample data for {country_name}: {e}")
            return {'error': str(e)}

# Global instance for use across the application
risk_service = RiskService()