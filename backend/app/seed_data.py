from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.country import Country

def seed_countries():
    """Seed the database with initial country data"""
    db = SessionLocal()
    
    # Check if countries already exist
    if db.query(Country).first():
        print("Countries already seeded")
        db.close()
        return
    
    countries = [
        Country(code="US", name="United States", region="North America", population=331900000),
        Country(code="CN", name="China", region="Asia", population=1439000000),
        Country(code="GB", name="United Kingdom", region="Europe", population=67800000),
        Country(code="DE", name="Germany", region="Europe", population=83200000),
        Country(code="BR", name="Brazil", region="South America", population=215300000),
        Country(code="IN", name="India", region="Asia", population=1380000000),
        Country(code="JP", name="Japan", region="Asia", population=125800000),
        Country(code="FR", name="France", region="Europe", population=65300000),
        Country(code="CA", name="Canada", region="North America", population=38000000),
        Country(code="AU", name="Australia", region="Oceania", population=25500000),
        Country(code="RU", name="Russia", region="Europe", population=145900000),
        Country(code="IT", name="Italy", region="Europe", population=60400000),
        Country(code="ES", name="Spain", region="Europe", population=46800000),
        Country(code="MX", name="Mexico", region="North America", population=128900000),
        Country(code="KR", name="South Korea", region="Asia", population=51800000),
        Country(code="TR", name="Turkey", region="Europe", population=84300000),
        Country(code="SA", name="Saudi Arabia", region="Middle East", population=34800000),
        Country(code="ZA", name="South Africa", region="Africa", population=59300000),
        Country(code="NG", name="Nigeria", region="Africa", population=206100000),
        Country(code="EG", name="Egypt", region="Africa", population=102300000),
    ]
    
    for country in countries:
        db.add(country)
    
    db.commit()
    print(f"Seeded {len(countries)} countries")
    db.close()

if __name__ == "__main__":
    seed_countries()