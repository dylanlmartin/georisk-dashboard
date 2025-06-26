# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Coding Instructions
Focus on writing concise, elegant code that completes tasks in as few lines of code as possible.  A human needs to be able to understand the entire codebase comprehensively, so each line of new code must be essential. Avoid code patterns that may cause elements of the project to fail silently.

## Architecture Overview

This is a full-stack geopolitical risk assessment dashboard with ML-based scoring capabilities:

- **Backend**: FastAPI (Python 3.11+) with async SQLAlchemy, PostgreSQL, Redis
- **Frontend**: React 18 + TypeScript + Material-UI with dark theme design system
- **ML Pipeline**: Random Forest + XGBoost ensemble models for risk prediction
- **Data Sources**: GDELT API, World Bank API, NewsAPI, Alpha Vantage (pre-configured with API keys)
- **Infrastructure**: Docker containerization with docker-compose orchestration

### Key Architectural Patterns

**Backend Services Architecture**:
- `gdelt_service.py`: Real-time geopolitical event collection from GDELT API
- `ml_risk_scoring_service.py`: Ensemble ML models (Random Forest + XGBoost) with confidence intervals
- `event_processing_service.py`: NLP processing and event classification
- `feature_engineering_service.py`: Time-series feature creation for ML models
- `worldbank_service.py`: Economic indicator collection

**Risk Scoring Systems**:
- **Legacy v1**: Rule-based weighted scoring (Political 35%, Economic 25%, Security 25%, Social 15%)
- **ML v2**: Ensemble models with bootstrap confidence intervals and component-specific predictions

**API Design**: Versioned REST API with legacy v1 endpoints and enhanced v2 ML-based endpoints

## Development Commands

### Full Stack Development
```bash
# Start entire application
docker-compose up

# Start with logs
docker-compose up --build

# Start individual services
docker-compose up backend frontend
docker-compose up postgres redis

# Stop all services
docker-compose down
```

### Backend Development
```bash
# Local development (requires PostgreSQL running)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run inside container for development
docker-compose exec backend uvicorn app.main:app --reload
```

### Frontend Development  
```bash
# Local development
cd frontend
npm install
npm start          # Development server on :3000
npm run build      # Production build
npm test           # Jest test runner
```

### Database Operations
```bash
# Seed initial data (countries, risk scores)
docker-compose exec backend python app/seed_data.py

# Run database migrations
docker-compose exec backend python app/simple_migration.py

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d georisk
```

## Key Data Models

- **Country**: Core entity with ISO codes, regions, population data
- **RiskScoreV2**: ML-based risk scores with confidence intervals and component breakdown
- **RawEvent/ProcessedEvent**: GDELT event pipeline from collection to analysis
- **FeatureVector**: Engineered features for ML model input (economic indicators, event aggregations)
- **EconomicIndicator**: World Bank governance and economic data

## API Endpoints Structure

**Access Points**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432 (postgres/postgres)

**Key API Patterns**:
- `/api/v1/countries` - Legacy rule-based risk scoring
- `/api/v2/risk-scores` - ML-based risk scoring with confidence intervals
- `/api/v2/countries/{code}/events` - Country-specific event analysis
- `/api/v2/risk-scores/trends` - Time-series risk analysis

## ML Model Architecture

**Ensemble Approach**: Random Forest + XGBoost for each risk component
- Models stored as pickle files in backend
- Bootstrap aggregation for confidence intervals  
- Component-specific predictions (political, economic, security, social)
- Feature engineering from GDELT events and World Bank indicators

**Training Pipeline**: 
- Historical data from 2020-2024 with manually labeled risk events
- Feature vectors combine event sentiment, economic indicators, governance metrics
- Models retrained periodically with new data

## Frontend Architecture

**Component Structure**:
- `Dashboard.tsx`: Main overview with world map, top risks, trends, alerts
- `WorldMap.tsx`: Interactive Leaflet map with country risk visualization
- `CountryDetailWidget.tsx`: Modal with detailed country analysis and AI-generated insights
- `RiskChart.tsx`: Time-series visualization using Recharts

**Design System**: Dark theme with professional color palette, risk-based color coding, Material-UI theming

**State Management**: React hooks with axios-based API client in `services/api.ts`

## Environment Configuration

Pre-configured API keys are included in docker-compose.yml:
- NEWS_API_KEY: 45bcda3489a3401a84bddfbd25e2d7cb
- ALPHA_VANTAGE_KEY: dl0xiquIOp5il0f2JmDEDhViaSX2tCWW

Rate limits:
- GDELT API: 1000 requests/day
- World Bank API: 10,000 requests/day  
- NewsAPI: 1000 requests/day
- Alpha Vantage: 25 requests/day

## Database Schema

Uses SQLAlchemy with async session management. Key tables:
- `countries`: Core country data with ISO codes
- `risk_scores_v2`: ML predictions with confidence bounds
- `raw_events`, `processed_events`: GDELT event pipeline
- `feature_vectors`: ML model input features
- `economic_indicators`: World Bank data

Database migrations in `backend/app/database/migrations/` with manual SQL scripts.

## Testing

Frontend uses Jest with react-scripts test runner. No backend testing framework currently configured.