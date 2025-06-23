from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.expanded_countries import EXPANDED_COUNTRIES, HIGH_PRIORITY_COUNTRIES, MEDIUM_PRIORITY_COUNTRIES
from datetime import datetime, timedelta
import random

def seed_countries():
    """Seed the database with initial country data"""
    db = SessionLocal()
    
    # Check if countries already exist
    if db.query(Country).first():
        print("Countries already seeded")
        db.close()
        return
    
    # Create Country objects from the expanded list
    countries = [
        Country(
            code=country_data["code"],
            name=country_data["name"],
            region=country_data["region"],
            population=country_data["population"]
        )
        for country_data in EXPANDED_COUNTRIES
    ]
    
    for country in countries:
        db.add(country)
    
    db.commit()
    print(f"Seeded {len(countries)} countries")
    db.close()

def seed_risk_scores():
    """Seed the database with sample risk score data"""
    db = SessionLocal()
    
    # Check if risk scores already exist
    if db.query(RiskScore).first():
        print("Risk scores already seeded")
        db.close()
        return
    
    countries = db.query(Country).all()
    if not countries:
        print("No countries found. Seed countries first.")
        db.close()
        return
    
    # Generate sample risk scores for the last 30 days
    risk_scores = []
    base_date = datetime.utcnow() - timedelta(days=30)
    
    for country in countries:
        # Generate different risk levels for different countries
        base_risk = random.randint(20, 80)
        
        for day in range(30):
            date = base_date + timedelta(days=day)
            
            # Add some variation to the base risk
            political_score = max(0, min(100, base_risk + random.randint(-10, 10)))
            economic_score = max(0, min(100, base_risk + random.randint(-15, 15)))
            security_score = max(0, min(100, base_risk + random.randint(-20, 20)))
            social_score = max(0, min(100, base_risk + random.randint(-5, 5)))
            
            # Calculate overall score using the weighted formula
            overall_score = (
                political_score * 0.35 +
                economic_score * 0.25 +
                security_score * 0.25 +
                social_score * 0.15
            )
            
            risk_score = RiskScore(
                country_code=country.code,
                overall_score=round(overall_score, 2),
                political_score=political_score,
                economic_score=economic_score,
                security_score=security_score,
                social_score=social_score,
                confidence_level=85.0,
                timestamp=date
            )
            risk_scores.append(risk_score)
    
    for score in risk_scores:
        db.add(score)
    
    db.commit()
    print(f"Seeded {len(risk_scores)} risk scores")
    db.close()

def seed_priority_countries():
    """Seed only high and medium priority countries first"""
    db = SessionLocal()
    
    # Check if countries already exist
    if db.query(Country).first():
        print("Countries already seeded")
        db.close()
        return
    
    # Filter to priority countries only
    priority_codes = set(HIGH_PRIORITY_COUNTRIES + MEDIUM_PRIORITY_COUNTRIES)
    priority_countries = [
        country_data for country_data in EXPANDED_COUNTRIES 
        if country_data["code"] in priority_codes
    ]
    
    countries = [
        Country(
            code=country_data["code"],
            name=country_data["name"],
            region=country_data["region"],
            population=country_data["population"]
        )
        for country_data in priority_countries
    ]
    
    for country in countries:
        db.add(country)
    
    db.commit()
    print(f"Seeded {len(countries)} priority countries")
    db.close()

if __name__ == "__main__":
    seed_countries()  # Full country list
    # seed_priority_countries()  # Uncomment to seed only priority countries
    seed_risk_scores()