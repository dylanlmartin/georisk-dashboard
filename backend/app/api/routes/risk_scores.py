from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.risk_score import RiskScore
from app.models.country import Country

router = APIRouter()

@router.get("/risk-scores/top-risks")
async def get_top_risk_countries(limit: Optional[int] = 10, db: Session = Depends(get_db)):
    """Get countries with highest current risk scores"""
    
    # Subquery to get latest risk score for each country
    latest_scores = db.query(
        RiskScore.country_code,
        func.max(RiskScore.timestamp).label('latest_timestamp')
    ).group_by(RiskScore.country_code).subquery()
    
    # Join with main table to get full risk score data
    top_risks = db.query(RiskScore, Country).join(
        latest_scores,
        (RiskScore.country_code == latest_scores.c.country_code) &
        (RiskScore.timestamp == latest_scores.c.latest_timestamp)
    ).join(Country, RiskScore.country_code == Country.code).order_by(
        desc(RiskScore.overall_score)
    ).limit(limit).all()
    
    result = []
    for risk_score, country in top_risks:
        result.append({
            "country_code": country.code,
            "country_name": country.name,
            "region": country.region,
            "overall_score": risk_score.overall_score,
            "political_score": risk_score.political_score,
            "economic_score": risk_score.economic_score,
            "security_score": risk_score.security_score,
            "social_score": risk_score.social_score,
            "confidence_level": risk_score.confidence_level,
            "timestamp": risk_score.timestamp
        })
    
    return result

@router.get("/risk-scores/alerts")
async def get_risk_alerts(hours: Optional[int] = 24, db: Session = Depends(get_db)):
    """Get countries with significant risk changes in the specified time period"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all risk scores within the time period
    recent_scores = db.query(RiskScore, Country).join(
        Country, RiskScore.country_code == Country.code
    ).filter(
        RiskScore.timestamp >= cutoff_time
    ).order_by(RiskScore.country_code, RiskScore.timestamp).all()
    
    alerts = []
    current_country = None
    country_scores = []
    
    for risk_score, country in recent_scores:
        if current_country != risk_score.country_code:
            # Process previous country's scores
            if current_country and len(country_scores) >= 2:
                alerts.extend(_detect_risk_changes(country_scores, 10.0))  # 10 point threshold
            
            # Start new country
            current_country = risk_score.country_code
            country_scores = [(risk_score, country)]
        else:
            country_scores.append((risk_score, country))
    
    # Process last country
    if current_country and len(country_scores) >= 2:
        alerts.extend(_detect_risk_changes(country_scores, 10.0))
    
    return sorted(alerts, key=lambda x: x['change_magnitude'], reverse=True)

@router.get("/risk-scores/trends")
async def get_risk_trends(days: Optional[int] = 7, db: Session = Depends(get_db)):
    """Get risk score trends across all countries"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get average risk scores by day
    daily_averages = db.query(
        func.date(RiskScore.timestamp).label('date'),
        func.avg(RiskScore.overall_score).label('avg_overall'),
        func.avg(RiskScore.political_score).label('avg_political'),
        func.avg(RiskScore.economic_score).label('avg_economic'),
        func.avg(RiskScore.security_score).label('avg_security'),
        func.avg(RiskScore.social_score).label('avg_social'),
        func.count(RiskScore.id).label('score_count')
    ).filter(
        RiskScore.timestamp >= cutoff_date
    ).group_by(
        func.date(RiskScore.timestamp)
    ).order_by(
        func.date(RiskScore.timestamp)
    ).all()
    
    trends = []
    for day in daily_averages:
        trends.append({
            "date": day.date,
            "average_overall_score": round(float(day.avg_overall), 2),
            "average_political_score": round(float(day.avg_political), 2),
            "average_economic_score": round(float(day.avg_economic), 2),
            "average_security_score": round(float(day.avg_security), 2),
            "average_social_score": round(float(day.avg_social), 2),
            "countries_updated": day.score_count
        })
    
    return {
        "period_days": days,
        "trends": trends
    }

@router.get("/risk-scores/regions")
async def get_regional_risk_summary(db: Session = Depends(get_db)):
    """Get risk score summary by geographic region"""
    
    # Subquery for latest scores
    latest_scores = db.query(
        RiskScore.country_code,
        func.max(RiskScore.timestamp).label('latest_timestamp')
    ).group_by(RiskScore.country_code).subquery()
    
    # Regional averages
    regional_data = db.query(
        Country.region,
        func.avg(RiskScore.overall_score).label('avg_overall'),
        func.avg(RiskScore.political_score).label('avg_political'),
        func.avg(RiskScore.economic_score).label('avg_economic'),
        func.avg(RiskScore.security_score).label('avg_security'),
        func.avg(RiskScore.social_score).label('avg_social'),
        func.count(Country.code).label('country_count')
    ).join(
        latest_scores, Country.code == latest_scores.c.country_code
    ).join(
        RiskScore,
        (RiskScore.country_code == latest_scores.c.country_code) &
        (RiskScore.timestamp == latest_scores.c.latest_timestamp)
    ).group_by(Country.region).all()
    
    regions = []
    for region in regional_data:
        regions.append({
            "region": region.region,
            "average_overall_score": round(float(region.avg_overall), 2),
            "average_political_score": round(float(region.avg_political), 2),
            "average_economic_score": round(float(region.avg_economic), 2),
            "average_security_score": round(float(region.avg_security), 2),
            "average_social_score": round(float(region.avg_social), 2),
            "country_count": region.country_count
        })
    
    return sorted(regions, key=lambda x: x['average_overall_score'], reverse=True)

def _detect_risk_changes(country_scores: List, threshold: float) -> List[dict]:
    """Helper function to detect significant risk changes"""
    alerts = []
    
    if len(country_scores) < 2:
        return alerts
    
    # Compare latest score with previous ones
    latest_score, latest_country = country_scores[-1]
    
    for i in range(len(country_scores) - 2, -1, -1):
        prev_score, _ = country_scores[i]
        
        change = latest_score.overall_score - prev_score.overall_score
        
        if abs(change) >= threshold:
            alerts.append({
                "country_code": latest_country.code,
                "country_name": latest_country.name,
                "previous_score": prev_score.overall_score,
                "current_score": latest_score.overall_score,
                "change": change,
                "change_magnitude": abs(change),
                "direction": "increase" if change > 0 else "decrease",
                "previous_timestamp": prev_score.timestamp,
                "current_timestamp": latest_score.timestamp,
                "alert_type": "significant_change"
            })
            break  # Only report one change per country
    
    return alerts