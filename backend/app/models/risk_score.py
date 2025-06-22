from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("countries.code"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    overall_score = Column(Float, nullable=False)
    political_score = Column(Float, nullable=False)
    economic_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    social_score = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)
    
    country = relationship("Country", backref="risk_scores")