from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class FeatureVector(Base):
    """Engineered features for ML pipeline"""
    __tablename__ = "feature_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), index=True)
    feature_date = Column(Date, nullable=False, index=True)
    features = Column(JSON)  # All engineered features as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="feature_vectors")