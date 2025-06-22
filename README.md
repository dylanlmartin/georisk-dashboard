# Geopolitical Risk Dashboard

A full-stack web application that tracks geopolitical risk scores across countries using real-time data from news APIs and economic indicators.

## Features

- **Real-time Risk Scoring**: Calculates quantitative risk scores (0-100) based on political, economic, security, and social factors
- **Interactive Dashboard**: View global risk overview with world map visualization
- **Country Details**: Deep dive into individual country risk assessments and trends
- **Historical Data**: Track risk score changes over time
- **Risk Alerts**: Get notified of significant risk changes
- **Data Sources**: NewsAPI.org, World Bank API, Alpha Vantage API

## Technology Stack

### Backend
- **FastAPI**: Python web framework for APIs
- **PostgreSQL**: Database for storing risk scores and news events
- **SQLAlchemy**: ORM for database operations
- **Redis**: Caching and task queue
- **VADER Sentiment**: News sentiment analysis
- **AsyncIO**: Asynchronous data collection

### Frontend
- **React**: UI framework with TypeScript
- **Material-UI**: Component library
- **Recharts**: Data visualization
- **React Router**: Navigation
- **Axios**: API client

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration

## Quick Start

### Prerequisites
- Docker and Docker Compose
- API Keys (optional for full functionality):
  - NewsAPI.org account
  - Alpha Vantage account

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/dylanlmartin/georisk-dashboard.git
   cd georisk-dashboard
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (optional)
   ```

3. **Start the application**
   ```bash
   docker-compose up
   ```

4. **Seed initial data**
   ```bash
   docker-compose exec backend python app/seed_data.py
   ```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/postgres)

## Risk Calculation Methodology

The system calculates overall risk scores using weighted categories:

- **Political Risk (35%)**: Based on news sentiment about elections, government, policy
- **Economic Risk (25%)**: GDP growth, inflation, debt ratios, currency volatility  
- **Security Risk (25%)**: Conflict mentions, terrorism, violence in news
- **Social Risk (15%)**: Protest activity, social unrest indicators

**Formula**: `overall_score = (political × 0.35) + (economic × 0.25) + (security × 0.25) + (social × 0.15)`

## API Endpoints

### Countries
- `GET /api/v1/countries` - List all countries with latest risk scores
- `GET /api/v1/countries/{code}` - Country details with recent events
- `GET /api/v1/countries/{code}/history` - Historical risk scores
- `POST /api/v1/countries/{code}/refresh` - Trigger data refresh

### Risk Scores
- `GET /api/v1/risk-scores/top-risks` - Countries with highest risk
- `GET /api/v1/risk-scores/alerts` - Recent significant changes
- `GET /api/v1/risk-scores/trends` - Global risk trends
- `GET /api/v1/risk-scores/regions` - Risk summary by region

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Database Management
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

## Data Sources

### Free APIs Used
1. **NewsAPI.org** (1,000 requests/day)
   - Global news headlines
   - Sentiment analysis source

2. **World Bank API** (Unlimited)
   - GDP growth rates
   - Inflation data
   - Unemployment rates
   - Debt-to-GDP ratios

3. **Alpha Vantage** (25 requests/day)
   - Currency exchange rates
   - Volatility calculations

## Deployment

### Production Environment
- Recommended: AWS/GCP with managed PostgreSQL
- Configure environment variables for production
- Set up CI/CD pipeline with GitHub Actions
- Enable SSL/TLS certificates

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/georisk
REDIS_URL=redis://host:6379
NEWS_API_KEY=your_newsapi_key
ALPHA_VANTAGE_KEY=your_alphavantage_key  
SECRET_KEY=your-secret-key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Roadmap

### Phase 1: Core Backend ✅
- [x] FastAPI setup with PostgreSQL
- [x] Risk calculation engine
- [x] Data collection services
- [x] Basic API endpoints

### Phase 2: Data Pipeline (In Progress)
- [ ] Background task scheduling
- [ ] WebSocket real-time updates
- [ ] Enhanced error handling
- [ ] Data quality scoring

### Phase 3: Frontend Dashboard (In Progress)
- [x] React app with TypeScript
- [x] Basic dashboard components
- [ ] Interactive world map
- [ ] Advanced charting
- [ ] Mobile responsive design

### Phase 4: Production Features
- [ ] PDF report generation
- [ ] CSV data export
- [ ] Performance optimization
- [ ] Monitoring and logging
- [ ] Cloud deployment

## Support

For questions or issues:
- Create an issue in this repository
- Check the API documentation at `/docs`
- Review the specification in `spec/geopolitical_mvp_spec.md`