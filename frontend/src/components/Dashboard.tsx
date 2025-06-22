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
import { Country, RiskAlert } from '../types';
import apiService from '../services/api';
import WorldMap from './WorldMap';
import RiskChart from './RiskChart';

const Dashboard: React.FC = () => {
  const [countries, setCountries] = useState<Country[]>([]);
  const [topRisks, setTopRisks] = useState<Country[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
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
    if (score >= 70) return '#d32f2f'; // High risk - red
    if (score >= 50) return '#f57c00'; // Medium risk - orange
    if (score >= 30) return '#fbc02d'; // Low-medium risk - yellow
    return '#388e3c'; // Low risk - green
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

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        Geopolitical Risk Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* World Map */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Global Risk Overview
            </Typography>
            <WorldMap countries={countries} />
          </Paper>
        </Grid>

        {/* Top Risk Countries */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Highest Risk Countries
            </Typography>
            <List>
              {topRisks.map((country, index) => (
                <ListItem key={country.code} divider>
                  <ListItemText
                    primary={`${index + 1}. ${country.name}`}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Chip
                          label={`${country.latest_risk_score?.overall_score?.toFixed(1) || 'N/A'}`}
                          sx={{
                            backgroundColor: getRiskColor(country.latest_risk_score?.overall_score || 0),
                            color: 'white',
                            mr: 1,
                          }}
                          size="small"
                        />
                        <Typography variant="caption">
                          {getRiskLevel(country.latest_risk_score?.overall_score || 0)} Risk
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