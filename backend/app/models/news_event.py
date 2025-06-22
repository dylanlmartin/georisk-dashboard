from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class NewsEvent(Base):
    __tablename__ = "news_events"
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("countries.code"), nullable=False)
    headline = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    published_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    country = relationship("Country", backref="news_events")