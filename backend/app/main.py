from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from app.database import get_db, engine
from app.models.country import Country
from app.models.risk_score import RiskScore  
from app.models.news_event import NewsEvent
from app.api.routes import countries, risk_scores
from app.database import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Geopolitical Risk Dashboard API",
    description="API for tracking geopolitical risk scores across countries",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(countries.router, prefix="/api/v1", tags=["countries"])
app.include_router(risk_scores.router, prefix="/api/v1", tags=["risk-scores"])

@app.get("/")
async def root():
    return {"message": "Geopolitical Risk Dashboard API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)