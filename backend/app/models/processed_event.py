from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ProcessedEvent(Base):
    """NLP-processed events with risk classification"""
    __tablename__ = "processed_events"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_event_id = Column(Integer, ForeignKey("raw_events.id"))
    risk_category = Column(String(20), index=True)  # conflict, protest, diplomatic, economic
    sentiment_score = Column(DECIMAL(5, 2))  # -1 to 1
    severity_score = Column(DECIMAL(5, 2))   # 0 to 1
    confidence = Column(DECIMAL(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    raw_event = relationship("RawEvent", back_populates="processed_event")