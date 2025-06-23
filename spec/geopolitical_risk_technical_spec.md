# Geopolitical Risk Scoring System - Technical Specification

## System Architecture

**Architecture Pattern:** Microservices with async data pipeline
**Tech Stack:** Python 3.11+, FastAPI, PostgreSQL, Redis, Docker
**Deployment:** Containerized with docker-compose for MVP

### Core Components
1. **Data Ingestion Service** - Async collectors for external APIs
2. **Event Processing Service** - NLP and event classification
3. **Feature Engineering Service** - Time-series and network feature creation
4. **ML Pipeline Service** - Model training and prediction
5. **Risk Scoring Service** - Composite score calculation
6. **API Gateway** - REST endpoints for client access
7. **Scheduler Service** - Automated data updates and model retraining

## Data Sources (Free APIs)

### Primary Sources
| Source | API Endpoint | Rate Limit | Key Required | Usage |
|--------|--------------|------------|--------------|-------|
| GDELT | `https://api.gdeltproject.org/api/v2` | 1000/day | No | Real-time events |
| World Bank | `https://api.worldbank.org/v2` | 10000/day | No | Economic indicators |
| NewsAPI | `https://newsapi.org/v2` | 1000/day | Yes (Free) | News sentiment |
| REST Countries | `https://restcountries.com/v3.1` | No limit | No | Country metadata |

### GDELT API Specifications
- **Endpoint:** `/doc/doc` for event articles
- **Parameters:** 
  - `query`: "country:{ISO_CODE} sourcelang:eng"
  - `mode`: "artlist"
  - `timespan`: "7d" (configurable)
  - `maxrecords`: 250 (max per request)
- **Response:** JSON array with title, url, seendate, socialimage, domain, language
- **Rate Limiting:** Implement 86.4 second delays between requests

### World Bank API Specifications
- **Endpoint:** `/country/{country}/indicator/{indicator}`
- **Key Indicators:**
  - Political Stability: `PV.EST`
  - Government Effectiveness: `GE.EST`
  - Regulatory Quality: `RQ.EST`
  - Rule of Law: `RL.EST`
  - Control of Corruption: `CC.EST`
- **Parameters:** `format=json&date=2020:2024&per_page=500`
- **Rate Limiting:** 8.64 second delays between requests

## Database Schema

### PostgreSQL Tables

**countries**
```
id: SERIAL PRIMARY KEY
iso_code: VARCHAR(3) UNIQUE NOT NULL
name: VARCHAR(100) NOT NULL
region: VARCHAR(50)
income_group: VARCHAR(50)
population: BIGINT
created_at: TIMESTAMP DEFAULT NOW()
```

**raw_events**
```
id: SERIAL PRIMARY KEY
country_id: INTEGER REFERENCES countries(id)
event_date: DATE NOT NULL
title: TEXT
source_url: TEXT
domain: VARCHAR(100)
language: VARCHAR(10)
tone: DECIMAL(5,2)
created_at: TIMESTAMP DEFAULT NOW()
INDEX ON (country_id, event_date)
```

**processed_events**
```
id: SERIAL PRIMARY KEY
raw_event_id: INTEGER REFERENCES raw_events(id)
risk_category: VARCHAR(20) -- conflict, protest, diplomatic, economic
sentiment_score: DECIMAL(5,2) -- -1 to 1
severity_score: DECIMAL(5,2) -- 0 to 1
confidence: DECIMAL(5,2)
created_at: TIMESTAMP DEFAULT NOW()
```

**economic_indicators**
```
id: SERIAL PRIMARY KEY
country_id: INTEGER REFERENCES countries(id)
indicator_code: VARCHAR(20)
year: INTEGER
value: DECIMAL(15,4)
created_at: TIMESTAMP DEFAULT NOW()
UNIQUE(country_id, indicator_code, year)
```

**feature_vectors**
```
id: SERIAL PRIMARY KEY
country_id: INTEGER REFERENCES countries(id)
feature_date: DATE NOT NULL
features: JSONB -- All engineered features as JSON
created_at: TIMESTAMP DEFAULT NOW()
INDEX ON (country_id, feature_date)
```

**risk_scores**
```
id: SERIAL PRIMARY KEY
country_id: INTEGER REFERENCES countries(id)
score_date: DATE NOT NULL
overall_score: DECIMAL(5,2)
political_stability_score: DECIMAL(5,2)
conflict_risk_score: DECIMAL(5,2)
economic_risk_score: DECIMAL(5,2)
institutional_quality_score: DECIMAL(5,2)
spillover_risk_score: DECIMAL(5,2)
confidence_lower: DECIMAL(5,2)
confidence_upper: DECIMAL(5,2)
model_version: VARCHAR(10)
created_at: TIMESTAMP DEFAULT NOW()
UNIQUE(country_id, score_date)
```

## Data Processing Pipeline

### 1. Data Ingestion Specifications

**Collection Schedule:**
- GDELT events: Every 6 hours
- World Bank indicators: Weekly
- News sentiment: Daily
- Feature engineering: Daily after event collection
- Risk scoring: Daily after feature engineering

**Rate Limiting Implementation:**
- Use Redis to track API call timestamps
- Implement exponential backoff for API errors
- Queue failed requests for retry with 5-minute delays

**Data Validation Rules:**
- Reject events with null country_id or event_date
- Validate ISO country codes against reference table
- Sanitize URLs and text content
- Flag duplicate events within 24-hour windows

### 2. Event Processing Specifications

**NLP Pipeline:**
- Use TextBlob for basic sentiment analysis (simple, no API keys required)
- Implement regex patterns for event classification:
  - Conflict: `/\b(attack|violence|fight|battle|war|conflict|assault|military)\b/i`
  - Protest: `/\b(protest|demonstration|rally|march|strike|riot)\b/i`
  - Diplomatic: `/\b(meeting|summit|negotiation|treaty|agreement|talks)\b/i`
  - Economic: `/\b(trade|economic|sanctions|embargo|tariff|commerce)\b/i`

**Severity Scoring Algorithm:**
- Base severity: 0.5
- Adjust for negative sentiment: `severity += abs(min(0, sentiment_score)) * 0.3`
- Adjust for conflict keywords: `severity += conflict_keyword_count * 0.1`
- Clamp to [0, 1] range

**Event Aggregation:**
- Group events by country and 7-day rolling windows
- Calculate metrics: event_count, avg_sentiment, severity_max, trend_slope

### 3. Feature Engineering Specifications

**Time Series Features (for periods: 7d, 30d, 90d, 365d):**
- `conflict_events_{period}`: Count of conflict events
- `protest_events_{period}`: Count of protest events
- `avg_sentiment_{period}`: Mean sentiment score
- `sentiment_volatility_{period}`: Standard deviation of sentiment
- `event_trend_{period}`: Linear regression slope of daily event counts
- `severity_max_{period}`: Maximum severity score in period

**Economic Features:**
- `{indicator}_latest`: Most recent value
- `{indicator}_yoy_change`: Year-over-year percentage change
- `{indicator}_volatility`: 3-year standard deviation
- `{indicator}_trend`: 3-year linear trend slope

**Network Features (Simplified for MVP):**
- `trade_dependence`: Placeholder value 0.5
- `alliance_strength`: Placeholder value 0.5
- `regional_instability`: Average risk score of neighboring countries

### 4. Machine Learning Pipeline Specifications

**Model Architecture:**
- **Random Forest:** 100 trees, max_depth=10, min_samples_split=5
- **XGBoost:** 100 estimators, learning_rate=0.1, max_depth=6
- **Ensemble:** Average predictions from both models

**Training Data Requirements:**
- Minimum 200 country-date observations per model
- Features: 50+ engineered features per observation
- Targets: Risk scores on 0-100 scale
- Validation: 5-fold time series cross-validation

**Model Components:**
1. **Political Stability Model** - Predicts government stability risk
2. **Conflict Risk Model** - Predicts violence/war probability
3. **Economic Risk Model** - Predicts economic disruption risk
4. **Institutional Quality Model** - Predicts governance effectiveness

**Composite Scoring:**
```
Overall Score = (
    Political Stability × 0.25 +
    Conflict Risk × 0.30 +
    Economic Risk × 0.25 +
    Institutional Quality × 0.20
)
```

**Confidence Intervals:**
- Use Random Forest individual tree predictions for variance estimation
- Calculate 95% confidence intervals: `prediction ± 1.96 × std_deviation`

## API Specifications

### REST Endpoints

**Base URL:** `http://localhost:8000/api/v1`

#### GET `/countries`
**Response:**
```json
{
  "countries": [
    {
      "iso_code": "USA",
      "name": "United States",
      "region": "North America"
    }
  ]
}
```

#### GET `/risk-scores/{country_code}`
**Parameters:**
- `country_code`: ISO 3-letter code (required)
- `date`: YYYY-MM-DD (optional, defaults to latest)

**Response:**
```json
{
  "country_code": "USA",
  "country_name": "United States",
  "score_date": "2024-01-15",
  "overall_score": 23.4,
  "component_scores": {
    "political_stability": 20.1,
    "conflict_risk": 15.2,
    "economic_risk": 35.8,
    "institutional_quality": 18.9
  },
  "confidence_intervals": {
    "overall": {"lower": 18.7, "upper": 28.1},
    "political_stability": {"lower": 15.3, "upper": 24.9}
  },
  "model_version": "1.0",
  "last_updated": "2024-01-15T08:00:00Z"
}
```

#### GET `/risk-scores/bulk`
**Parameters:**
- `countries`: Comma-separated ISO codes
- `date`: YYYY-MM-DD (optional)

**Response:** Array of risk score objects

#### GET `/trends/{country_code}`
**Parameters:**
- `country_code`: ISO 3-letter code
- `days`: Number of days (default: 30, max: 365)

**Response:**
```json
{
  "country_code": "USA",
  "trend_data": [
    {
      "date": "2024-01-01",
      "overall_score": 22.1,
      "component_scores": {...}
    }
  ]
}
```

#### GET `/events/{country_code}`
**Parameters:**
- `country_code`: ISO 3-letter code
- `days`: Number of days back (default: 7, max: 30)
- `category`: Filter by risk category (optional)

**Response:**
```json
{
  "country_code": "USA",
  "events": [
    {
      "date": "2024-01-15",
      "title": "Economic summit announced",
      "category": "diplomatic",
      "sentiment": 0.3,
      "severity": 0.2,
      "source_url": "https://..."
    }
  ]
}
```

### Error Handling
- **400 Bad Request:** Invalid parameters
- **404 Not Found:** Country not found
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Processing error

**Error Response Format:**
```json
{
  "error": "Country not found",
  "code": "COUNTRY_NOT_FOUND",
  "details": "ISO code 'XYZ' is not valid"
}
```

## Implementation Requirements

### Environment Setup
- **Python:** 3.11+ with asyncio support
- **Database:** PostgreSQL 15+ with JSONB support
- **Cache:** Redis 7+ for rate limiting and caching
- **ML Libraries:** scikit-learn, xgboost, pandas, numpy
- **NLP Libraries:** textblob, nltk
- **Web Framework:** FastAPI with uvicorn

### Configuration Management
```
config/
├── development.env
├── production.env
└── docker-compose.yml

Environment Variables:
- DATABASE_URL
- REDIS_URL
- NEWS_API_KEY
- LOG_LEVEL
- API_RATE_LIMITS
```

### Deployment Architecture
```
Docker Services:
├── api (FastAPI application)
├── worker (Background tasks)
├── postgres (Database)
├── redis (Cache/Queue)
└── nginx (Reverse proxy - production)
```

### Monitoring & Logging
- **Health Checks:** `/health` endpoint with database connectivity
- **Metrics:** Request count, response time, error rate
- **Logging:** Structured JSON logs with correlation IDs
- **Alerts:** Model performance degradation, API failures

### Security Requirements
- **Rate Limiting:** 100 requests/hour per IP for public endpoints
- **Input Validation:** Sanitize all user inputs
- **API Keys:** Optional authentication for premium features
- **CORS:** Configure for frontend domain

### Performance Requirements
- **Response Time:** <500ms for single country risk scores
- **Throughput:** Handle 1000 requests/hour sustained
- **Data Freshness:** Risk scores updated within 24 hours
- **Availability:** 99% uptime target

This specification provides sufficient technical detail for implementation while using only free APIs and open-source technologies suitable for an MVP deployment.