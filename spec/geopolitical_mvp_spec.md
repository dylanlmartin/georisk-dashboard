# Geopolitical Risk Dashboard - Claude Code Implementation Spec

## Project Overview
Build a full-stack geopolitical risk dashboard that collects data from free APIs, calculates quantitative risk scores, and displays them in an interactive web interface.

**Stack**: FastAPI (Python) + React (TypeScript) + PostgreSQL + Docker
**Timeline**: 16 weeks, implement incrementally
**Goal**: MVP for market validation using free data sources

---

## Project Structure
```
georisk-dashboard/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── main.py         # FastAPI app with startup tasks
│   │   ├── models/         # SQLAlchemy models (Country, RiskScore, NewsEvent)
│   │   ├── api/routes/     # API endpoints (/countries, /risk-scores, /alerts)
│   │   ├── core/           # Risk calculation engine & data collector
│   │   └── database.py     # PostgreSQL connection
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Dashboard, WorldMap, Charts, CountryDetail
│   │   ├── services/       # API client using axios
│   │   └── types/          # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Full stack with PostgreSQL & Redis
└── .env.example           # API keys and config
```

---

## Core Features to Implement

### 1. Risk Scoring Engine (`backend/app/core/risk_engine.py`)
Calculate 0-100 risk scores with weighted categories:
- **Political Risk (35%)**: News sentiment about elections, government, policy
- **Economic Risk (25%)**: GDP growth, inflation, debt ratios, currency volatility
- **Security Risk (25%)**: Conflict mentions, terrorism, violence in news
- **Social Risk (15%)**: Protest activity, social unrest indicators

**Algorithm**: 
```python
overall_score = (political * 0.35) + (economic * 0.25) + (security * 0.25) + (social * 0.15)
confidence_level = data_quality_score based on source diversity and freshness
```

### 2. Data Collection Service (`backend/app/core/data_collector.py`)
Async data collection from free APIs:

**News Data**: NewsAPI.org (1,000 requests/day)
- Collect headlines mentioning country names
- Apply VADER sentiment analysis
- Calculate relevance scores

**Economic Data**: World Bank API (unlimited)
- GDP growth, inflation, unemployment, debt-to-GDP ratios
- Most recent available values

**Market Data**: Alpha Vantage (25 requests/day)
- Currency exchange rates for volatility calculation

**Collection Strategy**: 
- Hourly updates for priority countries (batch of 10)
- Rate limiting with exponential backoff
- Store raw data + processed scores in database

### 3. Database Models (SQLAlchemy)

**Countries Table**:
```sql
countries: id, code(2-char), name, region, population
```

**Risk Scores Table** (time series):
```sql
risk_scores: id, country_code, timestamp, overall_score, political_score, 
economic_score, security_score, social_score, confidence_level
```

**News Events Table**:
```sql
news_events: id, country_code, headline, source, sentiment_score, 
published_at, processed_at
```

### 4. API Endpoints

**GET /api/v1/countries** - List all countries with latest risk scores
**GET /api/v1/countries/{code}** - Country details + recent events + historical data
**GET /api/v1/countries/{code}/history** - Historical risk scores with date filtering
**WebSocket /api/v1/realtime** - Real-time risk score updates

### 5. Frontend Components

**Dashboard Layout**:
- Interactive world map (react-leaflet) with color-coded risk levels
- Top 10 highest risk countries list
- Risk trend charts (recharts) for selected countries
- Recent alerts for significant risk changes (>10 points)

**Country Detail View**:
- Current risk breakdown by category
- 6-month historical trend chart
- Recent news events with sentiment
- Risk factor explanations

**Technologies**: React + TypeScript + Material-UI + recharts + react-leaflet

---

## Implementation Phases

### Phase 1: Core Backend (Weeks 1-4)
1. Set up FastAPI app with PostgreSQL connection
2. Create database models and migrations
3. Implement risk calculation algorithms
4. Build data collection service for NewsAPI + World Bank
5. Create basic API endpoints for countries and risk scores

### Phase 2: Data Pipeline (Weeks 5-8)
1. Add background tasks for periodic data collection
2. Implement sentiment analysis using VADER
3. Add error handling and rate limiting
4. Create data quality scoring
5. Add WebSocket support for real-time updates

### Phase 3: Frontend Dashboard (Weeks 9-12)
1. React app setup with TypeScript + Material-UI
2. API client service with react-query
3. Interactive world map with risk visualization
4. Country detail pages with charts
5. Responsive design for mobile

### Phase 4: Polish & Deploy (Weeks 13-16)
1. Docker containerization
2. Add export functionality (PDF reports, CSV data)
3. Performance optimization and caching
4. Error monitoring and logging
5. Production deployment to cloud

---

## Key Technical Requirements

### Environment Variables (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/georisk
REDIS_URL=redis://localhost:6379
NEWS_API_KEY=your_newsapi_key
ALPHA_VANTAGE_KEY=your_alphavantage_key
SECRET_KEY=jwt-secret-key
```

### Python Dependencies (requirements.txt)
```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
redis>=5.0.0
celery>=5.3.0
pandas>=2.1.0
numpy>=1.25.0
requests>=2.31.0
aiohttp>=3.9.0
spacy>=3.7.0
textblob>=0.17.0
vaderSentiment>=3.3.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
```

### React Dependencies (package.json)
```
react>=18.2.0
typescript>=4.9.0
@mui/material>=5.11.0
@mui/icons-material>=5.11.0
recharts>=2.5.0
react-leaflet>=4.2.0
leaflet>=1.9.0
axios>=1.3.0
react-query>=3.39.0
react-router-dom>=6.9.0
```

### Docker Compose Services
- **postgres**: PostgreSQL 15 with persistent volume
- **redis**: Redis 7 for caching and task queue
- **backend**: FastAPI app with auto-reload
- **frontend**: React dev server with hot reload

---

## Data Processing Logic

### Risk Score Calculation Examples
```python
# Political Risk: Based on news sentiment
political_keywords = ['election', 'government', 'policy', 'political']
avg_sentiment = mean([article.sentiment for article in political_news])
political_score = 50 + (avg_sentiment * -25)  # -1 sentiment = 75 risk

# Economic Risk: Based on indicators
if gdp_growth < -5: gdp_risk = 80
elif gdp_growth < 0: gdp_risk = 60
else: gdp_risk = 25

if inflation > 20: inflation_risk = 85
elif inflation > 10: inflation_risk = 65
else: inflation_risk = 25

economic_score = mean([gdp_risk, inflation_risk, debt_risk, currency_risk])
```

### Data Collection Schedule
- **High Priority Countries** (US, CN, GB, DE, BR): Every hour
- **Medium Priority**: Every 4 hours  
- **Low Priority**: Daily
- **Rate Limiting**: Max 1 request/second to external APIs

### Real-time Updates
- Calculate new risk scores when fresh data arrives
- WebSocket notifications for changes >10 points
- Dashboard auto-refresh every 5 minutes

---

## Success Metrics & Validation

**Technical Metrics**:
- 50+ countries with daily risk score updates
- <200ms API response time for country data
- 99.5% uptime target
- Data freshness: scores updated within 4 hours

**Product Metrics**:
- Interactive world map with clickable countries
- Historical trends for 6+ months
- Export functionality (PDF reports, CSV data)
- Mobile-responsive design

**Business Validation**:
- Demo to 10+ potential users
- Collect feedback on risk methodology
- Measure user engagement (session time, feature usage)
- Assess willingness to pay for premium features

---

## Deployment & Operations

### Local Development
```bash
# Start all services
docker-compose up

# Backend runs at http://localhost:8000
# Frontend runs at http://localhost:3000
# PostgreSQL at localhost:5432
```

### Production Deployment
- **Cloud Platform**: AWS/GCP free tier initially
- **Database**: Managed PostgreSQL service
- **Monitoring**: Basic logging + health checks
- **CI/CD**: GitHub Actions for automated testing/deployment

### Cost Estimate
- **Development**: $160K (2 developers × 16 weeks)
- **Monthly Operations**: $800 (cloud hosting + API overages)
- **Free API Limits**: NewsAPI 1K requests/day, Alpha Vantage 25/day

---

## Implementation Notes for Claude Code

1. **Start with Phase 1**: Focus on backend API with basic risk calculation
2. **Use Async/Await**: All external API calls should be asynchronous
3. **Error Handling**: Graceful degradation when APIs are unavailable
4. **Database Migrations**: Use Alembic for schema changes
5. **Testing**: Include basic unit tests for risk calculation logic
6. **Documentation**: Auto-generate API docs with FastAPI
7. **Security**: Basic rate limiting and input validation

This specification provides the complete technical roadmap while allowing Claude Code to implement the specific code details and handle the iterative development process.