from sqlalchemy import Column, Integer, String, Date, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class RawEvent(Base):
    """Raw events from GDELT and other sources"""
    __tablename__ = "raw_events"
    
    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), index=True)
    event_date = Column(Date, nullable=False, index=True)
    title = Column(Text)
    source_url = Column(Text)
    domain = Column(String(100))
    language = Column(String(10))
    tone = Column(DECIMAL(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="raw_events")
    processed_event = relationship("ProcessedEvent", back_populates="raw_event", uselist=False)