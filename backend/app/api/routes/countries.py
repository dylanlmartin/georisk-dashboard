from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.risk_score_v2 import RiskScoreV2
from app.core.risk_service import risk_service
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
        # Get latest ML-based risk score from v2 table
        latest_score = db.query(RiskScoreV2).filter(
            RiskScoreV2.country_id == country.id
        ).order_by(desc(RiskScoreV2.score_date)).first()
        
        country_data = {
            "code": country.code,
            "name": country.name,
            "region": country.region,
            "population": country.population,
            "latest_risk_score": None
        }
        
        if latest_score:
            country_data["latest_risk_score"] = {
                "overall_score": float(latest_score.overall_score),
                "political_score": float(latest_score.political_stability_score),
                "economic_score": float(latest_score.economic_risk_score),
                "security_score": float(latest_score.conflict_risk_score),
                "social_score": float(latest_score.institutional_quality_score),
                "confidence_level": float((latest_score.confidence_lower + latest_score.confidence_upper) / 2),
                "timestamp": latest_score.score_date.isoformat()
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
            data['economic_data'],
            country.code
        )
        
        # Save new risk score (convert numpy types to Python types)
        new_score = RiskScore(
            country_code=country.code,
            timestamp=datetime.utcnow(),
            overall_score=float(risk_scores.overall),
            political_score=float(risk_scores.political),
            economic_score=float(risk_scores.economic),
            security_score=float(risk_scores.security),
            social_score=float(risk_scores.social),
            confidence_level=float(risk_scores.confidence)
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

@router.post("/countries/collect-real-data")
async def collect_real_data(
    country_codes: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """Collect real data from APIs for multiple countries"""
    try:
        result = await risk_service.update_country_risk_scores(country_codes)
        return {
            "message": "Real data collection completed",
            "results": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting real data: {str(e)}")

@router.get("/countries/{country_code}/test-data")
async def test_country_data_collection(country_code: str, db: Session = Depends(get_db)):
    """Test data collection for a single country without saving to database"""
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    try:
        result = await risk_service.collect_sample_data_for_country(country.name, country.code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing data collection: {str(e)}")

@router.get("/countries/{country_code}/analysis")
async def get_country_analysis(country_code: str, db: Session = Depends(get_db)):
    """Get AI-generated risk analysis for a specific country"""
    country = db.query(Country).filter(Country.code == country_code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Get latest risk score for context
    latest_score = db.query(RiskScoreV2).filter(
        RiskScoreV2.country_id == country.id
    ).order_by(desc(RiskScoreV2.score_date)).first()
    
    if not latest_score:
        # Fallback to legacy risk scores
        latest_score = db.query(RiskScore).filter(
            RiskScore.country_code == country.code
        ).order_by(desc(RiskScore.timestamp)).first()
    
    # Generate analysis based on country profile and risk scores
    analysis = generate_country_analysis(country, latest_score)
    
    return analysis

def generate_country_analysis(country: Country, latest_score) -> dict:
    """Generate AI-like analysis for a country based on its profile and risk scores"""
    
    # Determine risk level and extract scores based on model type
    if latest_score:
        overall_score = float(latest_score.overall_score)
        
        # Check if it's RiskScoreV2 or legacy RiskScore
        if hasattr(latest_score, 'political_stability_score'):
            # RiskScoreV2 model
            political_score = float(latest_score.political_stability_score)
            economic_score = float(latest_score.economic_risk_score)
            security_score = float(latest_score.conflict_risk_score)
            social_score = float(latest_score.institutional_quality_score)
        else:
            # Legacy RiskScore model
            political_score = float(latest_score.political_score)
            economic_score = float(latest_score.economic_score)
            security_score = float(latest_score.security_score)
            social_score = float(latest_score.social_score)
    else:
        overall_score = 50.0
        political_score = economic_score = security_score = social_score = 50.0
    
    # Risk level determination
    if overall_score >= 90:
        risk_level = "very high"
    elif overall_score >= 75:
        risk_level = "high"
    elif overall_score >= 60:
        risk_level = "medium-high"
    elif overall_score >= 45:
        risk_level = "medium"
    elif overall_score >= 30:
        risk_level = "low-medium"
    else:
        risk_level = "low"
    
    # Country-specific analysis templates
    country_profiles = {
        "United States": {
            "key_factors": ["Federal political dynamics", "Economic monetary policy", "International relations", "Domestic polarization"],
            "risks": ["Political polarization and governance gridlock", "Economic inequality and inflation pressures", "International tensions and trade disputes"],
            "stability": ["Strong institutional framework", "Diversified economy", "Military and security capabilities"],
            "outlook": "Political and economic cycles continue to drive short-term volatility while institutional resilience provides stability."
        },
        "China": {
            "key_factors": ["Central government policy direction", "Economic transition dynamics", "Regional tensions", "Social stability measures"],
            "risks": ["Economic growth slowdown", "Geopolitical tensions", "Internal governance challenges"],
            "stability": ["Centralized governance structure", "Economic development momentum", "Strategic planning capabilities"],
            "outlook": "Structural economic transitions and geopolitical positioning remain key factors for medium-term stability."
        },
        "Afghanistan": {
            "key_factors": ["Security and governance transition", "Economic reconstruction needs", "International engagement", "Social cohesion"],
            "risks": ["Ongoing security challenges", "Economic instability and humanitarian needs", "Political legitimacy questions"],
            "stability": ["Regional stakeholder interest", "International humanitarian support", "Cultural resilience"],
            "outlook": "Near-term challenges require sustained international engagement and internal capacity building."
        },
        "Germany": {
            "key_factors": ["European Union leadership role", "Economic competitiveness", "Energy transition", "Demographic changes"],
            "risks": ["Energy security and supply chain dependencies", "Economic competitiveness pressures", "Political coalition dynamics"],
            "stability": ["Strong institutional framework", "Economic diversification", "European integration benefits"],
            "outlook": "Economic and energy transitions present challenges while institutional strength supports adaptation."
        }
    }
    
    # Get country-specific profile or use default
    profile = country_profiles.get(country.name, {
        "key_factors": ["Political stability dynamics", "Economic development patterns", "Security environment", "Social cohesion factors"],
        "risks": ["Regional geopolitical tensions", "Economic vulnerabilities", "Governance challenges"],
        "stability": ["Institutional capacity", "Economic fundamentals", "International partnerships"],
        "outlook": "Current trends require continued monitoring of key indicators for strategic assessment."
    })
    
    # Generate region-specific insights
    region_insights = {
        "North America": "benefits from strong institutional frameworks and economic integration",
        "Europe": "operates within multilateral frameworks providing stability mechanisms",
        "Asia": "experiences rapid economic transformation with varying governance models",
        "Middle East": "faces complex geopolitical dynamics and economic diversification challenges",
        "Africa": "shows diverse development trajectories with significant growth potential",
        "South America": "balances economic development with political stability considerations",
        "Oceania": "maintains stable governance with strong international partnerships",
        "Central Asia": "navigates regional power dynamics and economic development priorities"
    }
    
    region_context = region_insights.get(country.region, "experiences unique regional dynamics")
    
    # Generate summary
    population_size = "large" if country.population > 100000000 else "medium" if country.population > 10000000 else "small"
    
    summary = f"{country.name} presents a {risk_level} risk environment with an overall score of {overall_score:.1f}. " \
              f"As a {population_size} {country.region} country, it {region_context}. " \
              f"Key risk drivers include political stability (score: {political_score:.1f}), " \
              f"economic conditions (score: {economic_score:.1f}), security environment (score: {security_score:.1f}), " \
              f"and social dynamics (score: {social_score:.1f})."
    
    return {
        "summary": summary,
        "key_drivers": profile["key_factors"],
        "risk_factors": profile["risks"],
        "stability_factors": profile["stability"],
        "outlook": profile["outlook"],
        "risk_level": risk_level,
        "generated_at": datetime.utcnow().isoformat()
    }