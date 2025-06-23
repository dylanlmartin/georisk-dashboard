from sqlalchemy import Column, String, Integer, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, index=True, nullable=False)  # Updated to 3 chars
    iso_code = Column(String(3), unique=True, index=True)  # New spec field
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    income_group = Column(String(50))  # New spec field
    population = Column(BigInteger, nullable=True)  # Changed to BigInteger
    
    # Relationships to new tables
    raw_events = relationship("RawEvent", back_populates="country")
    economic_indicators = relationship("EconomicIndicator", back_populates="country")
    feature_vectors = relationship("FeatureVector", back_populates="country")
    risk_scores_v2 = relationship("RiskScoreV2", back_populates="country")