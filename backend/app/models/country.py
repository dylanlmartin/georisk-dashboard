from sqlalchemy import Column, String, Integer
from app.database import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(2), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    population = Column(Integer, nullable=True)