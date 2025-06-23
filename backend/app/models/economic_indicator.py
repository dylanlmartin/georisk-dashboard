from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class EconomicIndicator(Base):
    """Economic indicators from World Bank"""
    __tablename__ = "economic_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), index=True)
    indicator_code = Column(String(20), index=True)
    year = Column(Integer)
    value = Column(DECIMAL(15, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="economic_indicators")