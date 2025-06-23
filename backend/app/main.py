from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import asyncio
import os

from app.database import get_db, engine
from app.models import *  # Import all models including new ones
from app.api.routes import countries, risk_scores
from app.api.routes.risk_scores_v2 import router as risk_scores_v2_router
from app.api.routes.health import router as health_router
from app.database import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Geopolitical Risk Dashboard API",
    description="Advanced ML-based geopolitical risk assessment system implementing GDELT, World Bank, and ensemble modeling",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(countries.router, prefix="/api/v1", tags=["countries-legacy"])
app.include_router(risk_scores.router, prefix="/api/v1", tags=["risk-scores-legacy"])
app.include_router(risk_scores_v2_router, tags=["risk-scores-v2"])
app.include_router(health_router, tags=["health"])

@app.get("/")
async def root():
    return {
        "message": "Geopolitical Risk Dashboard API v2.0", 
        "features": [
            "GDELT real-time event collection",
            "World Bank governance indicators",
            "ML-based risk scoring with Random Forest + XGBoost ensemble",
            "Confidence intervals and uncertainty quantification",
            "Automated data pipeline with scheduler"
        ],
        "documentation": "/docs"
    }

# Legacy health endpoint for backward compatibility
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)