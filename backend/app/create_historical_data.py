#!/usr/bin/env python3
"""
Generate historical risk scores and alerts for dashboard widgets
"""

import os
import random
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database setup
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/georisk")
engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)

def generate_historical_scores():
    """Generate historical risk scores for the last 30 days"""
    print("📊 Generating historical risk scores...")
    
    with SessionLocal() as session:
        try:
            # Get all countries with current scores
            result = session.execute(text("""
                SELECT country_id, overall_score, political_stability_score, 
                       conflict_risk_score, economic_risk_score, institutional_quality_score
                FROM risk_scores_v2 
                WHERE score_date = CURRENT_DATE
            """))
            current_scores = result.fetchall()
            
            # Generate scores for the last 30 days
            for days_ago in range(1, 31):  # 1 to 30 days ago
                target_date = date.today() - timedelta(days=days_ago)
                
                for country_id, overall, political, conflict, economic, institutional in current_scores:
                    # Convert decimal to float for calculations
                    overall = float(overall)
                    political = float(political)
                    conflict = float(conflict)
                    economic = float(economic)
                    institutional = float(institutional)
                    # Add some realistic variation to historical scores
                    # More variation further back in time
                    variation_factor = min(0.15, days_ago * 0.005)  # Up to 15% variation
                    
                    # Generate slightly different scores with some trend
                    trend_factor = random.uniform(-0.02, 0.02)  # Small trending component
                    noise_factor = random.uniform(-variation_factor, variation_factor)
                    
                    # Calculate historical scores with bounded variation
                    hist_overall = max(0, min(100, overall + (overall * (trend_factor + noise_factor))))
                    hist_political = max(0, min(100, political + (political * (trend_factor + noise_factor))))
                    hist_conflict = max(0, min(100, conflict + (conflict * (trend_factor + noise_factor))))
                    hist_economic = max(0, min(100, economic + (economic * (trend_factor + noise_factor))))
                    hist_institutional = max(0, min(100, institutional + (institutional * (trend_factor + noise_factor))))
                    
                    # Insert historical score
                    session.execute(text("""
                        INSERT INTO risk_scores_v2 (
                            country_id, score_date, overall_score,
                            political_stability_score, conflict_risk_score,
                            economic_risk_score, institutional_quality_score,
                            spillover_risk_score, confidence_lower, confidence_upper,
                            model_version
                        ) VALUES (
                            :country_id, :score_date, :overall_score,
                            :political_stability_score, :conflict_risk_score,
                            :economic_risk_score, :institutional_quality_score,
                            :spillover_risk_score, :confidence_lower, :confidence_upper,
                            :model_version
                        )
                        ON CONFLICT (country_id, score_date) DO NOTHING
                    """), {
                        "country_id": country_id,
                        "score_date": target_date,
                        "overall_score": round(hist_overall, 2),
                        "political_stability_score": round(hist_political, 2),
                        "conflict_risk_score": round(hist_conflict, 2),
                        "economic_risk_score": round(hist_economic, 2),
                        "institutional_quality_score": round(hist_institutional, 2),
                        "spillover_risk_score": 35.0,
                        "confidence_lower": max(0, hist_overall - 8),
                        "confidence_upper": min(100, hist_overall + 8),
                        "model_version": "hist_2.0"
                    })
            
            session.commit()
            print(f"✅ Generated historical scores for {len(current_scores)} countries over 30 days")
            
        except Exception as e:
            print(f"❌ Error generating historical scores: {str(e)}")
            session.rollback()
            raise

def generate_risk_alerts():
    """Generate risk alerts based on recent score changes"""
    print("🚨 Generating risk alerts...")
    
    with SessionLocal() as session:
        try:
            # Clear existing alerts first
            session.execute(text("DELETE FROM risk_alerts WHERE 1=1"))
            
            # Find countries with significant score changes in last 7 days
            result = session.execute(text("""
                WITH recent_scores AS (
                    SELECT 
                        rs.country_id,
                        c.name as country_name,
                        c.code as country_code,
                        rs.score_date,
                        rs.overall_score,
                        LAG(rs.overall_score, 1) OVER (
                            PARTITION BY rs.country_id 
                            ORDER BY rs.score_date
                        ) as prev_score,
                        LAG(rs.score_date, 1) OVER (
                            PARTITION BY rs.country_id 
                            ORDER BY rs.score_date
                        ) as prev_date
                    FROM risk_scores_v2 rs
                    JOIN countries c ON rs.country_id = c.id
                    WHERE rs.score_date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY rs.country_id, rs.score_date
                )
                SELECT 
                    country_id, country_name, country_code,
                    overall_score as current_score,
                    prev_score as previous_score,
                    score_date as current_date,
                    prev_date as previous_date,
                    (overall_score - prev_score) as change
                FROM recent_scores
                WHERE prev_score IS NOT NULL
                AND ABS(overall_score - prev_score) >= 2.0  -- Significant change threshold
                ORDER BY ABS(overall_score - prev_score) DESC
                LIMIT 20
            """))
            
            changes = result.fetchall()
            
            # Create some synthetic alerts for demonstration
            if not changes:
                # Generate some synthetic recent changes for demo purposes
                high_risk_countries = [
                    ("AF", "Afghanistan", 90.25),
                    ("IR", "Iran", 70.75), 
                    ("IQ", "Iraq", 70.25),
                    ("PK", "Pakistan", 66.5),
                    ("MM", "Myanmar", 69.5)
                ]
                
                synthetic_alerts = []
                for i, (code, name, current_score) in enumerate(high_risk_countries):
                    # Get country_id
                    country_result = session.execute(text(
                        "SELECT id FROM countries WHERE code = :code"
                    ), {"code": code})
                    country_row = country_result.fetchone()
                    
                    if country_row:
                        country_id = country_row[0]
                        
                        # Create realistic alerts
                        if code == "AF":  # Afghanistan - security deterioration
                            change = +5.2
                            alert_type = "security_deterioration"
                        elif code == "IR":  # Iran - economic sanctions impact
                            change = +3.8
                            alert_type = "economic_sanctions"
                        elif code == "IQ":  # Iraq - political instability
                            change = +2.1
                            alert_type = "political_instability"
                        elif code == "PK":  # Pakistan - decreasing risk
                            change = -2.7
                            alert_type = "improving_conditions"
                        elif code == "MM":  # Myanmar - ongoing crisis
                            change = +4.1
                            alert_type = "conflict_escalation"
                        
                        previous_score = current_score - change
                        direction = "increase" if change > 0 else "decrease"
                        
                        synthetic_alerts.append({
                            "country_id": country_id,
                            "country_code": code,
                            "country_name": name,
                            "previous_score": previous_score,
                            "current_score": current_score,
                            "change": change,
                            "change_magnitude": abs(change),
                            "direction": direction,
                            "previous_timestamp": date.today() - timedelta(days=2),
                            "current_timestamp": date.today(),
                            "alert_type": alert_type
                        })
                
                changes = synthetic_alerts
            
            # Insert alerts
            alerts_created = 0
            for change_data in changes[:10]:  # Limit to top 10 alerts
                try:
                    if isinstance(change_data, dict):
                        # Synthetic alert - use directly
                        alert_data = {
                            "country_code": change_data["country_code"],
                            "country_name": change_data["country_name"],
                            "previous_score": change_data["previous_score"],
                            "current_score": change_data["current_score"],
                            "change": change_data["change"],
                            "change_magnitude": change_data["change_magnitude"],
                            "direction": change_data["direction"],
                            "previous_timestamp": change_data["previous_timestamp"],
                            "current_timestamp": change_data["current_timestamp"],
                            "alert_type": change_data["alert_type"]
                        }
                    else:
                        # Real database result
                        (country_id, country_name, country_code, current_score, 
                         previous_score, current_date, previous_date, change) = change_data
                        
                        alert_data = {
                            "country_code": country_code,
                            "country_name": country_name,
                            "previous_score": float(previous_score),
                            "current_score": float(current_score),
                            "change": float(change),
                            "change_magnitude": abs(float(change)),
                            "direction": "increase" if change > 0 else "decrease",
                            "previous_timestamp": previous_date,
                            "current_timestamp": current_date,
                            "alert_type": "significant_change"
                        }
                    
                    session.execute(text("""
                        INSERT INTO risk_alerts (
                            country_code, country_name, previous_score, current_score,
                            change, change_magnitude, direction, 
                            previous_timestamp, current_timestamp_value, alert_type
                        ) VALUES (
                            :country_code, :country_name, :previous_score, :current_score,
                            :change, :change_magnitude, :direction,
                            :previous_timestamp, :current_timestamp, :alert_type
                        )
                    """), alert_data)
                    
                    alerts_created += 1
                    
                except Exception as e:
                    print(f"Warning: Error creating alert: {str(e)}")
                    continue
            
            session.commit()
            print(f"✅ Generated {alerts_created} risk alerts")
            
        except Exception as e:
            print(f"❌ Error generating alerts: {str(e)}")
            session.rollback()
            raise

def create_risk_alerts_table():
    """Create the risk_alerts table if it doesn't exist"""
    print("📋 Creating risk_alerts table...")
    
    with SessionLocal() as session:
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS risk_alerts (
                    id SERIAL PRIMARY KEY,
                    country_code VARCHAR(3) NOT NULL,
                    country_name VARCHAR(100) NOT NULL,
                    previous_score DECIMAL(5,2),
                    current_score DECIMAL(5,2),
                    change DECIMAL(5,2),
                    change_magnitude DECIMAL(5,2),
                    direction VARCHAR(10),  -- 'increase' or 'decrease'
                    previous_timestamp TIMESTAMP,
                    current_timestamp_value TIMESTAMP,
                    alert_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            session.commit()
            print("✅ Risk alerts table ready")
            
        except Exception as e:
            print(f"❌ Error creating alerts table: {str(e)}")
            session.rollback()
            raise

def run_historical_data_generation():
    """Run the complete historical data generation"""
    print("🚀 Starting historical data generation")
    
    try:
        create_risk_alerts_table()
        generate_historical_scores()
        generate_risk_alerts()
        
        print("✅ Historical data generation completed successfully!")
        print("")
        print("📊 Dashboard widgets now have data:")
        print("• Risk Trends: 30 days of historical scores")
        print("• Risk Alerts: Recent significant changes")
        print("• All countries have realistic score variations")
        
    except Exception as e:
        print(f"❌ Historical data generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_historical_data_generation()