from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import datetime, date, timedelta
import json

from ...database import get_db
from ...models import Country, RiskScoreV2, RawEvent, ProcessedEvent
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["risk-scores-v2"])

@router.get("/risk-scores/{country_code}")
async def get_risk_scores(
    country_code: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get risk scores for a specific country
    Implements technical specification API format
    """
    try:
        # Get country
        result = await db.execute(
            select(Country).where(
                (Country.code == country_code.upper()) | 
                (Country.iso_code == country_code.upper())
            )
        )
        country = result.scalar_one_or_none()
        
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        
        # Parse date or use latest
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            target_date = None
        
        # Get risk score
        query = select(RiskScoreV2).where(RiskScoreV2.country_id == country.id)
        
        if target_date:
            query = query.where(RiskScoreV2.score_date == target_date)
        else:
            query = query.order_by(desc(RiskScoreV2.score_date)).limit(1)
        
        result = await db.execute(query)
        risk_score = result.scalar_one_or_none()
        
        if not risk_score:
            raise HTTPException(
                status_code=404, 
                detail=f"No risk scores found for {country.name}" + 
                       (f" on {date}" if date else "")
            )
        
        return {
            "country_code": country.code or country.iso_code,
            "country_name": country.name,
            "score_date": risk_score.score_date.isoformat(),
            "overall_score": float(risk_score.overall_score),
            "component_scores": {
                "political_stability": float(risk_score.political_stability_score or 0),
                "conflict_risk": float(risk_score.conflict_risk_score or 0),
                "economic_risk": float(risk_score.economic_risk_score or 0),
                "institutional_quality": float(risk_score.institutional_quality_score or 0)
            },
            "confidence_intervals": {
                "overall": {
                    "lower": float(risk_score.confidence_lower or 0),
                    "upper": float(risk_score.confidence_upper or 0)
                }
            },
            "model_version": risk_score.model_version,
            "last_updated": risk_score.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk scores for {country_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/risk-scores/bulk")
async def get_bulk_risk_scores(
    countries: str = Query(..., description="Comma-separated ISO country codes"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get risk scores for multiple countries
    """
    try:
        country_codes = [code.strip().upper() for code in countries.split(",")]
        
        if len(country_codes) > 50:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Too many countries requested (max 50)")
        
        # Parse date
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        results = []
        
        for country_code in country_codes:
            try:
                # Get country
                result = await db.execute(
                    select(Country).where(
                        (Country.code == country_code) | 
                        (Country.iso_code == country_code)
                    )
                )
                country = result.scalar_one_or_none()
                
                if not country:
                    results.append({
                        "country_code": country_code,
                        "error": "Country not found"
                    })
                    continue
                
                # Get risk score
                query = select(RiskScoreV2).where(RiskScoreV2.country_id == country.id)
                
                if target_date:
                    query = query.where(RiskScoreV2.score_date == target_date)
                else:
                    query = query.order_by(desc(RiskScoreV2.score_date)).limit(1)
                
                result = await db.execute(query)
                risk_score = result.scalar_one_or_none()
                
                if not risk_score:
                    results.append({
                        "country_code": country_code,
                        "country_name": country.name,
                        "error": "No risk scores available"
                    })
                    continue
                
                results.append({
                    "country_code": country.code or country.iso_code,
                    "country_name": country.name,
                    "score_date": risk_score.score_date.isoformat(),
                    "overall_score": float(risk_score.overall_score),
                    "component_scores": {
                        "political_stability": float(risk_score.political_stability_score or 0),
                        "conflict_risk": float(risk_score.conflict_risk_score or 0),
                        "economic_risk": float(risk_score.economic_risk_score or 0),
                        "institutional_quality": float(risk_score.institutional_quality_score or 0)
                    },
                    "confidence_intervals": {
                        "overall": {
                            "lower": float(risk_score.confidence_lower or 0),
                            "upper": float(risk_score.confidence_upper or 0)
                        }
                    },
                    "model_version": risk_score.model_version,
                    "last_updated": risk_score.created_at.isoformat()
                })
                
            except Exception as e:
                logger.warning(f"Error processing {country_code}: {str(e)}")
                results.append({
                    "country_code": country_code,
                    "error": "Processing error"
                })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk risk scores: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends/{country_code}")
async def get_risk_trends(
    country_code: str,
    days: int = Query(30, ge=1, le=365, description="Number of days (1-365)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get risk score trends for a country over time
    """
    try:
        # Use direct database query to avoid all async issues
        import os
        import psycopg2
        
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/georisk")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend_data = []
        country_info = None
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Get country info first
                cur.execute("""
                    SELECT id, code, name FROM countries 
                    WHERE UPPER(code) = UPPER(%s) OR UPPER(iso_code) = UPPER(%s)
                """, (country_code, country_code))
                
                country_row = cur.fetchone()
                if not country_row:
                    raise HTTPException(status_code=404, detail="Country not found")
                
                country_id, country_code_actual, country_name = country_row
                country_info = {
                    "id": country_id,
                    "code": country_code_actual,
                    "name": country_name
                }
                
                # Get trend data
                cur.execute("""
                    SELECT score_date, overall_score, political_stability_score, 
                           conflict_risk_score, economic_risk_score, institutional_quality_score
                    FROM risk_scores_v2
                    WHERE country_id = %s 
                    AND score_date >= %s 
                    AND score_date <= %s
                    ORDER BY score_date
                """, (country_id, start_date, end_date))
                
                for row in cur.fetchall():
                    trend_data.append({
                        "date": row[0].isoformat(),
                        "overall_score": float(row[1]),
                        "component_scores": {
                            "political_stability": float(row[2] or 0),
                            "conflict_risk": float(row[3] or 0),
                            "economic_risk": float(row[4] or 0),
                            "institutional_quality": float(row[5] or 0)
                        }
                    })
        
        return {
            "country_code": country_info["code"],
            "country_name": country_info["name"],
            "period_days": days,
            "trend_data": trend_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trends for {country_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/events/{country_code}")
async def get_country_events(
    country_code: str,
    days: int = Query(7, ge=1, le=30, description="Number of days back (1-30)"),
    category: Optional[str] = Query(None, description="Filter by risk category"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent events for a country with risk classification
    """
    try:
        # Get country
        result = await db.execute(
            select(Country).where(
                (Country.code == country_code.upper()) | 
                (Country.iso_code == country_code.upper())
            )
        )
        country = result.scalar_one_or_none()
        
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = (
            select(RawEvent, ProcessedEvent)
            .outerjoin(ProcessedEvent)
            .where(
                and_(
                    RawEvent.country_id == country.id,
                    RawEvent.event_date >= start_date,
                    RawEvent.event_date <= end_date
                )
            )
        )
        
        if category:
            query = query.where(ProcessedEvent.risk_category == category.lower())
        
        query = query.order_by(desc(RawEvent.event_date))
        
        result = await db.execute(query)
        events = result.fetchall()
        
        event_list = []
        for raw_event, processed_event in events:
            event_data = {
                "date": raw_event.event_date.isoformat(),
                "title": raw_event.title,
                "source_url": raw_event.source_url,
                "domain": raw_event.domain
            }
            
            if processed_event:
                event_data.update({
                    "category": processed_event.risk_category,
                    "sentiment": float(processed_event.sentiment_score or 0),
                    "severity": float(processed_event.severity_score or 0),
                    "confidence": float(processed_event.confidence or 0)
                })
            else:
                event_data.update({
                    "category": "unprocessed",
                    "sentiment": 0.0,
                    "severity": 0.0,
                    "confidence": 0.0
                })
            
            event_list.append(event_data)
        
        return {
            "country_code": country.code or country.iso_code,
            "country_name": country.name,
            "period_days": days,
            "total_events": len(event_list),
            "events": event_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting events for {country_code}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/alerts")
async def get_risk_alerts(
    hours: int = Query(24, ge=1, le=168, description="Number of hours back (1-168)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of alerts (1-100)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent risk alerts based on significant score changes
    """
    try:
        from sqlalchemy import text
        import os
        import psycopg2
        
        # Use direct connection for now due to sync/async issues with raw SQL
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/georisk")
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Direct database query
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        country_code, country_name, previous_score, current_score,
                        change, change_magnitude, direction, 
                        previous_timestamp, current_timestamp_value, alert_type,
                        created_at
                    FROM risk_alerts 
                    WHERE created_at >= %s
                    ORDER BY change_magnitude DESC, created_at DESC
                    LIMIT %s
                """, (cutoff_time, limit))
                
                alerts = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
        
        alert_list = []
        for alert in alerts:
            # Convert tuple to dict using column names
            alert_dict = dict(zip(columns, alert))
            
            alert_list.append({
                "country_code": alert_dict["country_code"],
                "country_name": alert_dict["country_name"],
                "risk_change": {
                    "previous_score": float(alert_dict["previous_score"]),
                    "current_score": float(alert_dict["current_score"]),
                    "change": float(alert_dict["change"]),
                    "change_magnitude": float(alert_dict["change_magnitude"]),
                    "direction": alert_dict["direction"]
                },
                "timestamps": {
                    "previous": alert_dict["previous_timestamp"].isoformat() if alert_dict["previous_timestamp"] else None,
                    "current": alert_dict["current_timestamp_value"].isoformat() if alert_dict["current_timestamp_value"] else None
                },
                "alert_type": alert_dict["alert_type"],
                "created_at": alert_dict["created_at"].isoformat()
            })
        
        return {
            "alerts": alert_list,
            "total_alerts": len(alert_list),
            "period_hours": hours,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting risk alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/countries")
async def get_countries_v2(db: AsyncSession = Depends(get_db)):
    """
    Get list of all countries with latest risk scores
    Enhanced version with ML-based scores
    """
    try:
        # Get countries with their latest risk scores
        result = await db.execute(
            select(Country, RiskScoreV2)
            .outerjoin(RiskScoreV2)
            .order_by(Country.name, desc(RiskScoreV2.score_date))
        )
        
        # Group by country to get latest score for each
        countries_dict = {}
        for country, risk_score in result.fetchall():
            if country.id not in countries_dict:
                countries_dict[country.id] = {
                    "iso_code": country.code or country.iso_code,
                    "name": country.name,
                    "region": country.region,
                    "income_group": country.income_group,
                    "population": country.population,
                    "latest_risk_score": None
                }
            
            # Add latest risk score if available and not already set
            if (risk_score and 
                countries_dict[country.id]["latest_risk_score"] is None):
                countries_dict[country.id]["latest_risk_score"] = {
                    "overall_score": float(risk_score.overall_score),
                    "political_stability_score": float(risk_score.political_stability_score or 0),
                    "conflict_risk_score": float(risk_score.conflict_risk_score or 0),
                    "economic_risk_score": float(risk_score.economic_risk_score or 0),
                    "institutional_quality_score": float(risk_score.institutional_quality_score or 0),
                    "confidence_lower": float(risk_score.confidence_lower or 0),
                    "confidence_upper": float(risk_score.confidence_upper or 0),
                    "score_date": risk_score.score_date.isoformat(),
                    "model_version": risk_score.model_version
                }
        
        return {
            "countries": list(countries_dict.values()),
            "total_countries": len(countries_dict),
            "api_version": "v2"
        }
        
    except Exception as e:
        logger.error(f"Error getting countries: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")