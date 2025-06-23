import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import { CountryDetail as CountryDetailType, HistoricalData } from '../types/index.ts';
import apiService from '../services/api.ts';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CountryDetail: React.FC = () => {
  const { countryCode } = useParams<{ countryCode: string }>();
  const [country, setCountry] = useState<CountryDetailType | null>(null);
  const [history, setHistory] = useState<HistoricalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (countryCode) {
      loadCountryData(countryCode);
    }
  }, [countryCode]);

  const loadCountryData = async (code: string) => {
    try {
      const [countryData, historyData] = await Promise.all([
        apiService.getCountryDetails(code),
        apiService.getCountryHistory(code, 30),
      ]);
      setCountry(countryData);
      setHistory(historyData);
    } catch (error) {
      console.error('Error loading country data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!countryCode) return;
    
    setRefreshing(true);
    try {
      await apiService.refreshCountryData(countryCode);
      await loadCountryData(countryCode);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getRiskColor = (score: number): string => {
    if (score >= 70) return '#d32f2f';
    if (score >= 50) return '#f57c00';
    if (score >= 30) return '#fbc02d';
    return '#388e3c';
  };

  const getRiskLevel = (score: number): string => {
    if (score >= 70) return 'High';
    if (score >= 50) return 'Medium';
    if (score >= 30) return 'Low-Medium';
    return 'Low';
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!country) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">Country not found</Alert>
      </Container>
    );
  }

  const riskScore = country.latest_risk_score;
  const chartData = history?.history.map(h => ({
    date: new Date(h.timestamp).toLocaleDateString(),
    overall: h.overall_score,
    political: h.political_score,
    economic: h.economic_score,
    security: h.security_score,
    social: h.social_score,
  })) || [];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button component={Link} to="/" startIcon={<ArrowBack />} sx={{ mr: 2 }}>
          Back to Dashboard
        </Button>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {country.name} ({country.code})
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh Data'}
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Country Info */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Country Information
            </Typography>
            <Typography><strong>Region:</strong> {country.region}</Typography>
            <Typography><strong>Population:</strong> {country.population?.toLocaleString()}</Typography>
            {riskScore && (
              <Box sx={{ mt: 2 }}>
                <Typography><strong>Last Updated:</strong></Typography>
                <Typography variant="body2" color="text.secondary">
                  {new Date(riskScore.timestamp).toLocaleString()}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Risk Scores */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Current Risk Assessment
            </Typography>
            {riskScore ? (
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={4}>
                  <Box textAlign="center">
                    <Typography variant="h3" sx={{ color: getRiskColor(riskScore.overall_score) }}>
                      {riskScore.overall_score.toFixed(1)}
                    </Typography>
                    <Typography variant="h6">Overall Risk</Typography>
                    <Chip 
                      label={getRiskLevel(riskScore.overall_score)} 
                      sx={{ backgroundColor: getRiskColor(riskScore.overall_score), color: 'white' }}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={8}>
                  <Grid container spacing={1}>
                    {[
                      { label: 'Political', value: riskScore.political_score },
                      { label: 'Economic', value: riskScore.economic_score },
                      { label: 'Security', value: riskScore.security_score },
                      { label: 'Social', value: riskScore.social_score },
                    ].map((item, index) => (
                      <Grid item xs={6} key={index}>
                        <Box textAlign="center" sx={{ p: 1 }}>
                          <Typography variant="h5">{item.value.toFixed(1)}</Typography>
                          <Typography variant="body2">{item.label}</Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      <strong>Confidence Level:</strong> {riskScore.confidence_level.toFixed(1)}%
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            ) : (
              <Alert severity="info">No risk assessment available yet</Alert>
            )}
          </Paper>
        </Grid>

        {/* Historical Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Risk Trends (Last 30 Days)
            </Typography>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="90%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="overall" stroke="#1976d2" strokeWidth={3} name="Overall" />
                  <Line type="monotone" dataKey="political" stroke="#9c27b0" name="Political" />
                  <Line type="monotone" dataKey="economic" stroke="#f57c00" name="Economic" />
                  <Line type="monotone" dataKey="security" stroke="#d32f2f" name="Security" />
                  <Line type="monotone" dataKey="social" stroke="#388e3c" name="Social" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '90%' }}>
                <Typography color="text.secondary">
                  No historical data available
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Recent News */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Events (Last 7 Days)
            </Typography>
            {country.recent_news && country.recent_news.length > 0 ? (
              <List>
                {country.recent_news.map((news, index) => (
                  <ListItem key={index} divider>
                    <ListItemText
                      primary={news.headline}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            Source: {news.source}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(news.published_at).toLocaleString()}
                          </Typography>
                          <Chip
                            size="small"
                            label={`Sentiment: ${news.sentiment_score.toFixed(2)}`}
                            sx={{ ml: 1, fontSize: '0.7rem' }}
                          />
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="text.secondary">
                No recent news events available
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default CountryDetail;