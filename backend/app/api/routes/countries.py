from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.news_event import NewsEvent
from app.core.data_collector import DataCollector
from app.core.risk_engine import RiskEngine

router = APIRouter()

@router.get("/countries", response_model=List[dict])
async def get_countries(db: Session = Depends(get_db)):
    """Get all countries with their latest risk scores"""
    countries = db.query(Country).all()
    result = []
    
    for country in countries:
        # Get latest risk score
        latest_score = db.query(RiskScore).filter(
            RiskScore.country_code == country.code
        ).order_by(desc(RiskScore.timestamp)).first()
        
        country_data = {
            "code": country.code,
            "name": country.name,
            "region": country.region,
            "population": country.population,
            "latest_risk_score": None
        }
        
        if latest_score:
            country_data["latest_risk_score"] = {
                "overall_score": latest_score.overall_score,
                "political_score": latest_score.political_score,
                "economic_score": latest_score.economic_score,
                "security_score": latest_score.security_score,
                "social_score": latest_score.social_score,
                "confidence_level": latest_score.confidence_level,
                "timestamp": latest_score.timestamp
            }
        
        result.append(country_data)
    
    return result

@router.get("/countries/{country_code}")
async def get_country_details(country_code: str, db: Session = Depends(get_db)):
    """Get detailed information for a specific country"""
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Get latest risk score
    latest_score = db.query(RiskScore).filter(
        RiskScore.country_code == country.code
    ).order_by(desc(RiskScore.timestamp)).first()
    
    # Get recent news events (last 7 days)
    recent_news = db.query(NewsEvent).filter(
        NewsEvent.country_code == country.code,
        NewsEvent.published_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(desc(NewsEvent.published_at)).limit(10).all()
    
    country_data = {
        "code": country.code,
        "name": country.name,
        "region": country.region,
        "population": country.population,
        "latest_risk_score": None,
        "recent_news": []
    }
    
    if latest_score:
        country_data["latest_risk_score"] = {
            "overall_score": latest_score.overall_score,
            "political_score": latest_score.political_score,
            "economic_score": latest_score.economic_score,
            "security_score": latest_score.security_score,
            "social_score": latest_score.social_score,
            "confidence_level": latest_score.confidence_level,
            "timestamp": latest_score.timestamp
        }
    
    for news in recent_news:
        country_data["recent_news"].append({
            "headline": news.headline,
            "source": news.source,
            "sentiment_score": news.sentiment_score,
            "published_at": news.published_at
        })
    
    return country_data

@router.get("/countries/{country_code}/history")
async def get_country_history(
    country_code: str, 
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """Get historical risk scores for a country"""
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Get historical risk scores
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    historical_scores = db.query(RiskScore).filter(
        RiskScore.country_code == country.code,
        RiskScore.timestamp >= cutoff_date
    ).order_by(RiskScore.timestamp).all()
    
    history = []
    for score in historical_scores:
        history.append({
            "timestamp": score.timestamp,
            "overall_score": score.overall_score,
            "political_score": score.political_score,
            "economic_score": score.economic_score,
            "security_score": score.security_score,
            "social_score": score.social_score,
            "confidence_level": score.confidence_level
        })
    
    return {
        "country_code": country.code,
        "country_name": country.name,
        "period_days": days,
        "history": history
    }

@router.post("/countries/{country_code}/refresh")
async def refresh_country_data(country_code: str, db: Session = Depends(get_db)):
    """Manually trigger data collection and risk calculation for a country"""
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    try:
        # Collect fresh data
        collector = DataCollector()
        data = await collector.collect_country_data(country.name, country.code)
        
        # Calculate risk scores
        risk_engine = RiskEngine()
        risk_scores = risk_engine.calculate_risk_scores(
            data['news_articles'], 
            data['economic_data']
        )
        
        # Save new risk score
        new_score = RiskScore(
            country_code=country.code,
            overall_score=risk_scores.overall,
            political_score=risk_scores.political,
            economic_score=risk_scores.economic,
            security_score=risk_scores.security,
            social_score=risk_scores.social,
            confidence_level=risk_scores.confidence
        )
        db.add(new_score)
        
        # Save news events
        for article in data['news_articles']:
            news_event = NewsEvent(
                country_code=country.code,
                headline=article['headline'],
                source=article['source'],
                sentiment_score=0.0,  # Will be calculated by risk engine
                published_at=article['published_at']
            )
            db.add(news_event)
        
        db.commit()
        
        return {
            "message": f"Successfully refreshed data for {country.name}",
            "risk_scores": {
                "overall": risk_scores.overall,
                "political": risk_scores.political,
                "economic": risk_scores.economic,
                "security": risk_scores.security,
                "social": risk_scores.social,
                "confidence": risk_scores.confidence
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error refreshing data: {str(e)}")