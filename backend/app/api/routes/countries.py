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
from app.models.processed_event import ProcessedEvent
from app.core.data_collector import DataCollector
from app.core.risk_engine import RiskEngine
from app.services.ai_analysis_service import AIAnalysisService

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
    
    # Get recent events for context (through raw_event relationship)
    from app.models.raw_event import RawEvent
    recent_events = db.query(ProcessedEvent).join(RawEvent).filter(
        RawEvent.country_id == country.id,
        RawEvent.event_date >= datetime.utcnow() - timedelta(days=30)
    ).order_by(desc(RawEvent.event_date)).limit(20).all()
    
    # Get historical trend (last 30 days)
    historical_scores = db.query(RiskScoreV2).filter(
        RiskScoreV2.country_id == country.id,
        RiskScoreV2.score_date >= datetime.utcnow() - timedelta(days=30)
    ).order_by(RiskScoreV2.score_date).all()
    
    # Generate AI-powered analysis
    ai_service = AIAnalysisService()
    analysis = await ai_service.generate_country_analysis(country, latest_score, recent_events, historical_scores)
    
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

def generate_dynamic_country_analysis(country: Country, latest_score, recent_events, historical_scores) -> dict:
    """Generate dynamic analysis based on current data and trends"""
    
    # Extract scores
    if latest_score:
        overall_score = float(latest_score.overall_score)
        if hasattr(latest_score, 'political_stability_score'):
            political_score = float(latest_score.political_stability_score)
            economic_score = float(latest_score.economic_risk_score)
            security_score = float(latest_score.conflict_risk_score)
            social_score = float(latest_score.institutional_quality_score)
        else:
            political_score = float(latest_score.political_score)
            economic_score = float(latest_score.economic_score)
            security_score = float(latest_score.security_score)
            social_score = float(latest_score.social_score)
    else:
        overall_score = political_score = economic_score = security_score = social_score = 50.0
    
    risk_level = ("very high" if overall_score >= 80 else "high" if overall_score >= 65 else 
                 "medium-high" if overall_score >= 50 else "medium" if overall_score >= 35 else 
                 "low-medium" if overall_score >= 20 else "low")
    
    # Calculate trend
    trend_direction = "stable"
    trend_magnitude = 0
    if len(historical_scores) >= 2:
        oldest_score = float(historical_scores[0].overall_score)
        newest_score = float(historical_scores[-1].overall_score)
        trend_magnitude = newest_score - oldest_score
        if trend_magnitude > 3:
            trend_direction = "increasing"
        elif trend_magnitude < -3:
            trend_direction = "decreasing"
    
    # Analyze events
    event_categories = {}
    if recent_events:
        for event in recent_events:
            category = getattr(event, 'risk_category', 'general')
            event_categories[category] = event_categories.get(category, 0) + 1
    
    # Generate dynamic factors based on scores
    key_factors = []
    if political_score > 60:
        key_factors.append("Political tensions and governance challenges")
    elif political_score < 40:
        key_factors.append("Political stability and institutional strength")
    else:
        key_factors.append("Political dynamics and governance evolution")
    
    if economic_score > 60:
        key_factors.append("Economic vulnerabilities and market pressures")
    elif economic_score < 40:
        key_factors.append("Economic resilience and growth fundamentals")
    else:
        key_factors.append("Economic development and structural transitions")
    
    if security_score > 60:
        key_factors.append("Security challenges and conflict risks")
    elif security_score < 40:
        key_factors.append("Security stability and defense capabilities")
    else:
        key_factors.append("Security environment and regional dynamics")
    
    if social_score > 60:
        key_factors.append("Social tensions and cohesion challenges")
    else:
        key_factors.append("Social stability and institutional development")
    
    # Risk factors based on highest scores
    risk_factors = []
    scores_dict = {"Political": political_score, "Economic": economic_score, 
                   "Security": security_score, "Social": social_score}
    high_risk_areas = [k for k, v in scores_dict.items() if v > 55]
    
    for area in high_risk_areas:
        risk_factors.append(f"{area} sector vulnerabilities and elevated risk indicators")
    
    if not risk_factors:
        risk_factors = ["Moderate risk levels across assessed dimensions"]
    
    # Stability factors
    stability_factors = []
    low_risk_areas = [k for k, v in scores_dict.items() if v < 45]
    for area in low_risk_areas:
        stability_factors.append(f"Relatively stable {area.lower()} environment")
    
    population_size = "large" if country.population > 100000000 else "medium" if country.population > 10000000 else "small"
    if population_size == "large":
        stability_factors.append("Large population providing economic scale")
    
    region_stability = {
        "North America": "Institutional frameworks and economic integration",
        "Europe": "Multilateral cooperation and democratic institutions", 
        "Asia": "Economic dynamism and regional partnerships",
        "Middle East": "Strategic importance and energy resources",
        "Africa": "Growth potential and natural resources",
        "South America": "Regional cooperation and resource wealth"
    }
    
    if country.region in region_stability:
        stability_factors.append(region_stability[country.region])
    
    if not stability_factors:
        stability_factors = ["Basic institutional capacity and international engagement"]
    
    # Generate outlook
    trend_text = "stable conditions" if trend_direction == "stable" else f"{trend_direction} risk trajectory"
    outlook_base = f"Current {trend_text} with {risk_level} overall risk levels suggest "
    
    if trend_direction == "increasing" and overall_score > 60:
        outlook_base += "heightened vigilance and proactive risk management are essential."
    elif trend_direction == "decreasing" and overall_score < 50:
        outlook_base += "improving conditions support positive medium-term prospects."
    else:
        outlook_base += "continued assessment of evolving conditions for strategic planning."
    
    # Generate summary
    region_context = {
        "North America": "benefits from institutional stability and economic integration",
        "Europe": "operates within established multilateral frameworks", 
        "Asia": "experiences dynamic economic and political transformation",
        "Middle East": "navigates complex regional dynamics and geopolitical tensions",
        "Africa": "pursues development amid diverse challenges and opportunities",
        "South America": "balances economic growth with political stability"
    }.get(country.region, "faces unique regional dynamics")
    
    summary = (f"{country.name} presents a {risk_level} risk environment with an overall score of {overall_score:.1f}. "
              f"As a {population_size} {country.region} nation, it {region_context}. "
              f"Risk assessment shows political: {political_score:.1f}, economic: {economic_score:.1f}, "
              f"security: {security_score:.1f}, social: {social_score:.1f}.")
    
    if trend_direction != "stable":
        summary += f" Risk levels are currently {trend_direction} by {abs(trend_magnitude):.1f} points."
    
    return {
        "summary": summary,
        "key_drivers": key_factors,
        "risk_factors": risk_factors,
        "stability_factors": stability_factors,
        "outlook": outlook_base,
        "risk_level": risk_level,
        "trend_direction": trend_direction,
        "trend_magnitude": round(trend_magnitude, 1),
        "recent_event_categories": list(event_categories.keys()) if event_categories else [],
        "generated_at": datetime.utcnow().isoformat()
    }