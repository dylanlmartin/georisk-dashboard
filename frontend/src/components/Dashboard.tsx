import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Country, RiskAlert } from '../types/index.ts';
import apiService from '../services/api.ts';
import WorldMap from './WorldMap.tsx';
import RiskChart from './RiskChart.tsx';

const Dashboard: React.FC = () => {
  const [countries, setCountries] = useState<Country[]>([]);
  const [topRisks, setTopRisks] = useState<Country[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [countriesData, topRisksData, alertsData] = await Promise.all([
        apiService.getCountries(),
        apiService.getTopRiskCountries(10),
        apiService.getRiskAlerts(24),
      ]);

      setCountries(countriesData);
      setTopRisks(topRisksData);
      setAlerts(alertsData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score: number): string => {
    if (score >= 70) return '#d32f2f'; // Red - Very High Risk
    if (score >= 60) return '#f44336'; // Red-Orange - High Risk
    if (score >= 50) return '#ff9800'; // Orange - Medium-High Risk
    if (score >= 40) return '#ffc107'; // Amber - Medium Risk
    if (score >= 30) return '#ffeb3b'; // Yellow - Low-Medium Risk
    return '#4caf50'; // Green - Low Risk
  };

  const getRiskLevel = (score: number): string => {
    if (score >= 70) return 'Very High';
    if (score >= 60) return 'High';
    if (score >= 50) return 'Medium-High';
    if (score >= 40) return 'Medium';
    if (score >= 30) return 'Low-Medium';
    return 'Low';
  };

  const handleCountryClick = (country: Country) => {
    setSelectedCountry(country);
    // Could add navigation to country detail page here
    console.log('Selected country:', country.name);
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        Geopolitical Risk Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* World Map */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 0, height: 600 }}>
            <WorldMap countries={countries} onCountryClick={handleCountryClick} />
          </Paper>
        </Grid>

        {/* Top Risk Countries */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Highest Risk Countries
            </Typography>
            <List>
              {topRisks.map((risk, index) => (
                <ListItem key={risk.country_code} divider>
                  <ListItemText
                    primary={`${index + 1}. ${risk.country_name || risk.name}`}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Chip
                          label={`${risk.overall_score?.toFixed(1) || 'N/A'}`}
                          sx={{
                            backgroundColor: getRiskColor(risk.overall_score || 0),
                            color: 'white',
                            mr: 1,
                          }}
                          size="small"
                        />
                        <Typography variant="caption">
                          {getRiskLevel(risk.overall_score || 0)} Risk
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Risk Trends Chart */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Risk Trends (Last 7 Days)
            </Typography>
            <RiskChart />
          </Paper>
        </Grid>

        {/* Recent Alerts */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Recent Risk Alerts
            </Typography>
            {alerts.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No significant risk changes detected
              </Typography>
            ) : (
              <List>
                {alerts.slice(0, 5).map((alert, index) => (
                  <ListItem key={index} divider>
                    <ListItemText
                      primary={alert.country_name}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {alert.direction === 'increase' ? '↗️' : '↘️'} 
                            {alert.change > 0 ? '+' : ''}{alert.change.toFixed(1)} points
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(alert.current_timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;