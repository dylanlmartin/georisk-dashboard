import axios from 'axios';
import { Country, CountryDetail, HistoricalData, RiskAlert } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
});

export const apiService = {
  // Countries
  getCountries: async (): Promise<Country[]> => {
    const response = await api.get('/countries');
    return response.data;
  },

  getCountryDetails: async (countryCode: string): Promise<CountryDetail> => {
    const response = await api.get(`/countries/${countryCode}`);
    return response.data;
  },

  getCountryHistory: async (countryCode: string, days: number = 30): Promise<HistoricalData> => {
    const response = await api.get(`/countries/${countryCode}/history?days=${days}`);
    return response.data;
  },

  refreshCountryData: async (countryCode: string): Promise<any> => {
    const response = await api.post(`/countries/${countryCode}/refresh`);
    return response.data;
  },

  // Risk Scores
  getTopRiskCountries: async (limit: number = 10): Promise<Country[]> => {
    const response = await api.get(`/risk-scores/top-risks?limit=${limit}`);
    return response.data;
  },

  getRiskAlerts: async (hours: number = 24): Promise<RiskAlert[]> => {
    const response = await api.get(`/risk-scores/alerts?hours=${hours}`);
    return response.data;
  },

  getRiskTrends: async (days: number = 7): Promise<any> => {
    const response = await api.get(`/risk-scores/trends?days=${days}`);
    return response.data;
  },

  getRegionalRiskSummary: async (): Promise<any> => {
    const response = await api.get('/risk-scores/regions');
    return response.data;
  },
};

export default apiService;