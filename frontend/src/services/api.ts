import axios from 'axios';
import { Country, CountryDetail, HistoricalData, RiskAlert } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
});

export const apiService = {
  // Countries (Updated to use v2 API with ML-based scores)
  getCountries: async (): Promise<Country[]> => {
    const response = await api.get('/countries');
    // Handle new v2 API response format
    if (response.data.countries) {
      return response.data.countries.map((country: any) => ({
        code: country.iso_code || country.code,
        name: country.name,
        region: country.region,
        population: country.population,
        latest_risk_score: country.latest_risk_score ? {
          overall_score: country.latest_risk_score.overall_score,
          political_score: country.latest_risk_score.political_stability_score,
          economic_score: country.latest_risk_score.economic_risk_score,
          security_score: country.latest_risk_score.conflict_risk_score,
          social_score: country.latest_risk_score.institutional_quality_score,
          confidence_level: ((country.latest_risk_score.confidence_lower + country.latest_risk_score.confidence_upper) / 2),
          timestamp: country.latest_risk_score.score_date
        } : null
      }));
    }
    return response.data;
  },

  getCountryDetails: async (countryCode: string): Promise<CountryDetail> => {
    const response = await api.get(`/countries/${countryCode}`);
    return response.data;
  },

  getCountryHistory: async (countryCode: string, days: number = 30): Promise<HistoricalData> => {
    // Use new v2 trends endpoint
    const response = await api.get(`/trends/${countryCode}?days=${days}`);
    return {
      country_code: response.data.country_code,
      country_name: response.data.country_name,
      period_days: response.data.period_days,
      history: response.data.trend_data.map((item: any) => ({
        overall_score: item.overall_score,
        political_score: item.component_scores.political_stability,
        economic_score: item.component_scores.economic_risk,
        security_score: item.component_scores.conflict_risk,
        social_score: item.component_scores.institutional_quality,
        confidence_level: 80, // Default confidence
        timestamp: item.date
      }))
    };
  },

  refreshCountryData: async (countryCode: string): Promise<any> => {
    const response = await api.post(`/countries/${countryCode}/refresh`);
    return response.data;
  },

  // Risk Scores (Updated to use ML-based system)
  getTopRiskCountries: async (limit: number = 10): Promise<Country[]> => {
    // Get all countries and sort by risk score
    const countries = await apiService.getCountries();
    const countriesWithScores = countries.filter(c => c.latest_risk_score);
    
    // Sort by overall score descending
    countriesWithScores.sort((a, b) => {
      const scoreA = a.latest_risk_score?.overall_score || 0;
      const scoreB = b.latest_risk_score?.overall_score || 0;
      return scoreB - scoreA;
    });
    
    return countriesWithScores.slice(0, limit).map(country => ({
      ...country,
      country_code: country.code,
      country_name: country.name,
      overall_score: country.latest_risk_score?.overall_score
    }));
  },

  getRiskAlerts: async (hours: number = 24): Promise<RiskAlert[]> => {
    const response = await api.get(`/alerts?hours=${hours}`);
    return response.data.alerts.map((alert: any) => ({
      id: `${alert.country_code}_${alert.created_at}`,
      country_code: alert.country_code,
      country_name: alert.country_name,
      previous_score: alert.risk_change.previous_score,
      current_score: alert.risk_change.current_score,
      change: alert.risk_change.change,
      direction: alert.risk_change.direction, // Fix: Extract direction from nested object
      change_type: alert.alert_type,
      current_timestamp: alert.created_at, // Fix: Use correct field name
      timestamp: alert.created_at,
      severity: alert.risk_change.change_magnitude > 5 ? 'high' : 
               alert.risk_change.change_magnitude > 2 ? 'medium' : 'low'
    }));
  },

  getRiskTrends: async (days: number = 7): Promise<any> => {
    // Get trends for top risk countries
    const countries = await apiService.getTopRiskCountries(10);
    const allTrends: any[] = [];
    
    // Collect trends from top 5 countries
    for (const country of countries.slice(0, 5)) {
      try {
        const response = await api.get(`/trends/${country.code}?days=${days}`);
        allTrends.push(response.data);
      } catch (error) {
        console.warn(`Failed to get trends for ${country.code}:`, error);
      }
    }
    
    // Aggregate data by date
    const dateMap: { [date: string]: any[] } = {};
    
    allTrends.forEach(countryTrend => {
      countryTrend.trend_data.forEach((dataPoint: any) => {
        if (!dateMap[dataPoint.date]) {
          dateMap[dataPoint.date] = [];
        }
        dateMap[dataPoint.date].push(dataPoint);
      });
    });
    
    // Calculate averages for each date
    const trends = Object.keys(dateMap)
      .sort()
      .map(date => {
        const dataPoints = dateMap[date];
        const averages = {
          date,
          average_overall_score: dataPoints.reduce((sum, dp) => sum + dp.overall_score, 0) / dataPoints.length,
          average_political_score: dataPoints.reduce((sum, dp) => sum + dp.component_scores.political_stability, 0) / dataPoints.length,
          average_economic_score: dataPoints.reduce((sum, dp) => sum + dp.component_scores.economic_risk, 0) / dataPoints.length,
          average_security_score: dataPoints.reduce((sum, dp) => sum + dp.component_scores.conflict_risk, 0) / dataPoints.length,
          average_social_score: dataPoints.reduce((sum, dp) => sum + dp.component_scores.institutional_quality, 0) / dataPoints.length,
        };
        return averages;
      });
    
    return { trends };
  },

  getRegionalRiskSummary: async (): Promise<any> => {
    const response = await api.get('/risk-scores/regions');
    return response.data;
  },

  // New v2 API methods
  getRiskScoresV2: async (countryCode: string, date?: string): Promise<any> => {
    const url = `/risk-scores/${countryCode}${date ? `?date=${date}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  getCountryEvents: async (countryCode: string, days: number = 7, category?: string): Promise<any> => {
    const url = `/events/${countryCode}?days=${days}${category ? `&category=${category}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  getCountryAnalysis: async (countryCode: string): Promise<any> => {
    const response = await api.get(`/countries/${countryCode}/analysis`);
    return response.data;
  }
};

export default apiService;