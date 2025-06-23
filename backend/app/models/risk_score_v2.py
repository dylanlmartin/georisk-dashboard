from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RiskScoreV2(Base):
    """New ML-based risk scores with confidence intervals"""
    __tablename__ = "risk_scores_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), index=True)
    score_date = Column(Date, nullable=False, index=True)
    overall_score = Column(DECIMAL(5, 2))
    political_stability_score = Column(DECIMAL(5, 2))
    conflict_risk_score = Column(DECIMAL(5, 2))
    economic_risk_score = Column(DECIMAL(5, 2))
    institutional_quality_score = Column(DECIMAL(5, 2))
    spillover_risk_score = Column(DECIMAL(5, 2))  
    confidence_lower = Column(DECIMAL(5, 2))
    confidence_upper = Column(DECIMAL(5, 2))
    model_version = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="risk_scores_v2")