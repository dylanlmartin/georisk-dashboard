export interface Country {
  code: string;
  name: string;
  region: string;
  population: number;
  latest_risk_score?: RiskScore;
}

export interface RiskScore {
  overall_score: number;
  political_score: number;
  economic_score: number;
  security_score: number;
  social_score: number;
  confidence_level: number;
  timestamp: string;
}

export interface NewsEvent {
  headline: string;
  source: string;
  sentiment_score: number;
  published_at: string;
}

export interface CountryDetail extends Country {
  recent_news: NewsEvent[];
}

export interface HistoricalData {
  country_code: string;
  country_name: string;
  period_days: number;
  history: RiskScore[];
}

export interface RiskAlert {
  country_code: string;
  country_name: string;
  previous_score: number;
  current_score: number;
  change: number;
  change_magnitude: number;
  direction: 'increase' | 'decrease';
  previous_timestamp: string;
  current_timestamp: string;
  alert_type: string;
}