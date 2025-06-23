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
  Avatar,
  styled,
} from '@mui/material';
import { TrendingUp, TrendingDown, Public, Warning } from '@mui/icons-material';
import { Country, RiskAlert } from '../types/index.ts';
import apiService from '../services/api.ts';
import WorldMap from './WorldMap.tsx';
import RiskChart from './RiskChart.tsx';
import { getRiskColor, getRiskLevel, getRiskGradient, designTokens } from '../theme/theme.ts';

// Styled components for modern design
const StyledContainer = styled(Container)(({ theme }) => ({
  background: `linear-gradient(180deg, ${designTokens.colors.background.primary} 0%, ${designTokens.colors.background.secondary} 100%)`,
  minHeight: '100vh',
  paddingTop: theme.spacing(6),
  paddingBottom: theme.spacing(6),
}));

const HeaderBox = styled(Box)(({ theme }) => ({
  textAlign: 'center',
  marginBottom: theme.spacing(6),
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '60px',
    height: '60px',
    background: `radial-gradient(circle, ${designTokens.colors.accent.primary}20 0%, transparent 70%)`,
    borderRadius: '50%',
    zIndex: -1,
  },
}));

const MapContainer = styled(Paper)(({ theme }) => ({
  padding: 0,
  height: '600px',
  overflow: 'hidden',
  background: designTokens.colors.background.primary,
  border: `1px solid ${designTokens.colors.border.subtle}`,
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `radial-gradient(ellipse at center, ${designTokens.colors.background.secondary}40 0%, transparent 70%)`,
    pointerEvents: 'none',
    zIndex: 1,
  },
}));

const RiskListItem = styled(ListItem)(({ theme }) => ({
  borderRadius: designTokens.borderRadius.small,
  marginBottom: theme.spacing(1),
  backgroundColor: `${designTokens.colors.background.elevated}30`,
  border: `1px solid ${designTokens.colors.border.subtle}`,
  transition: 'all 0.2s ease-out',
  '&:hover': {
    backgroundColor: designTokens.colors.background.elevated,
    transform: 'translateX(4px)',
    borderColor: designTokens.colors.border.emphasis,
  },
}));

const RankAvatar = styled(Avatar)<{ rank: number }>(({ theme, rank }) => ({
  width: 32,
  height: 32,
  fontSize: '0.875rem',
  fontWeight: 600,
  marginRight: theme.spacing(2),
  background: rank <= 3 
    ? `linear-gradient(135deg, ${designTokens.colors.risk.high}, ${designTokens.colors.risk.veryHigh})`
    : `linear-gradient(135deg, ${designTokens.colors.accent.primary}, ${designTokens.colors.accent.secondary})`,
}));

const RiskScoreChip = styled(Chip)<{ score: number }>(({ score }) => ({
  background: getRiskGradient(score),
  color: 'white',
  fontWeight: 600,
  fontSize: '0.75rem',
  border: `1px solid ${getRiskColor(score)}40`,
  '&::before': {
    content: '""',
    position: 'absolute',
    inset: 0,
    borderRadius: 'inherit',
    background: `linear-gradient(135deg, transparent 0%, ${getRiskColor(score)}20 100%)`,
  },
}));

const AlertItem = styled(ListItem)<{ direction: string }>(({ theme, direction }) => ({
  borderRadius: designTokens.borderRadius.small,
  marginBottom: theme.spacing(1),
  backgroundColor: direction === 'increase' 
    ? `${designTokens.colors.risk.veryHigh}10` 
    : `${designTokens.colors.risk.low}10`,
  border: `1px solid ${direction === 'increase' 
    ? designTokens.colors.risk.veryHigh + '30' 
    : designTokens.colors.risk.low + '30'}`,
  borderLeft: `4px solid ${direction === 'increase' 
    ? designTokens.colors.risk.veryHigh 
    : designTokens.colors.risk.low}`,
  transition: 'all 0.2s ease-out',
  '&:hover': {
    backgroundColor: direction === 'increase' 
      ? `${designTokens.colors.risk.veryHigh}20` 
      : `${designTokens.colors.risk.low}20`,
    transform: 'translateX(4px)',
  },
}));

const LoadingContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '60vh',
  gap: designTokens.spacing.large,
});

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


  const handleCountryClick = (country: Country) => {
    setSelectedCountry(country);
    // Could add navigation to country detail page here
    console.log('Selected country:', country.name);
  };

  if (loading) {
    return (
      <StyledContainer maxWidth="xl">
        <LoadingContainer>
          <CircularProgress 
            size={60} 
            sx={{ 
              color: designTokens.colors.accent.primary,
              '& .MuiCircularProgress-circle': {
                strokeLinecap: 'round',
              },
            }} 
          />
          <Typography variant="h6" color="text.secondary" sx={{ mt: 2 }}>
            Loading geopolitical risk data...
          </Typography>
        </LoadingContainer>
      </StyledContainer>
    );
  }

  return (
    <StyledContainer maxWidth="xl">
      <HeaderBox>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <Public sx={{ fontSize: 40, color: designTokens.colors.accent.primary, mr: 2 }} />
          <Typography 
            variant="h1" 
            component="h1" 
            sx={{ 
              background: `linear-gradient(135deg, ${designTokens.colors.text.primary} 0%, ${designTokens.colors.accent.primary} 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 700,
            }}
          >
            Geopolitical Risk Dashboard
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
          Real-time assessment of global political, economic, and security risks across 170 countries
        </Typography>
      </HeaderBox>

      <Grid container spacing={4}>
        {/* World Map */}
        <Grid item xs={12} lg={8}>
          <MapContainer>
            <Box sx={{ display: 'flex', alignItems: 'center', p: 3, zIndex: 2, position: 'relative' }}>
              <Typography variant="h4" sx={{ color: designTokens.colors.text.primary, fontWeight: 600 }}>
                Interactive Geopolitical Risk Map
              </Typography>
            </Box>
            <Box sx={{ position: 'relative', zIndex: 2 }}>
              {console.log('Dashboard: Passing countries to WorldMap. Length:', countries.length)}
              {console.log('Dashboard: Sample country:', countries[0])}
              <WorldMap countries={countries} onCountryClick={handleCountryClick} />
            </Box>
          </MapContainer>
        </Grid>

        {/* Top Risk Countries */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, height: 600, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Warning sx={{ color: designTokens.colors.risk.high, mr: 1 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Highest Risk Countries
              </Typography>
            </Box>
            <Box sx={{ flex: 1, overflow: 'auto', pr: 1 }}>
              <List sx={{ '& .MuiListItem-root': { px: 0 } }}>
                {topRisks.map((risk, index) => (
                  <RiskListItem key={risk.country_code}>
                    <RankAvatar rank={index + 1}>{index + 1}</RankAvatar>
                    <ListItemText
                      primary={
                        <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
                          {risk.country_name || risk.name}
                        </Typography>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <RiskScoreChip
                            label={`${risk.overall_score?.toFixed(1) || 'N/A'}`}
                            score={risk.overall_score || 0}
                            size="small"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {getRiskLevel(risk.overall_score || 0)} Risk
                          </Typography>
                        </Box>
                      }
                    />
                  </RiskListItem>
                ))}
              </List>
            </Box>
          </Paper>
        </Grid>

        {/* Risk Trends Chart */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, height: 450 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <TrendingUp sx={{ color: designTokens.colors.accent.primary, mr: 1 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Risk Trends (Last 7 Days)
              </Typography>
            </Box>
            <Box sx={{ height: 'calc(100% - 80px)' }}>
              <RiskChart />
            </Box>
          </Paper>
        </Grid>

        {/* Recent Alerts */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, height: 450, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <TrendingDown sx={{ color: designTokens.colors.risk.medium, mr: 1 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Recent Risk Alerts
              </Typography>
            </Box>
            <Box sx={{ flex: 1, overflow: 'auto', pr: 1 }}>
              {alerts.length === 0 ? (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  height: '100%',
                  color: 'text.secondary',
                  textAlign: 'center',
                }}>
                  <Warning sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    No significant risk changes detected
                  </Typography>
                  <Typography variant="caption">
                    Monitoring 170 countries for changes ≥2.0 points
                  </Typography>
                </Box>
              ) : (
                <List sx={{ '& .MuiListItem-root': { px: 0 } }}>
                  {alerts.slice(0, 5).map((alert, index) => (
                    <AlertItem key={index} direction={alert.direction}>
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        mr: 2,
                        color: alert.direction === 'increase' 
                          ? designTokens.colors.risk.veryHigh 
                          : designTokens.colors.risk.low
                      }}>
                        {alert.direction === 'increase' ? 
                          <TrendingUp sx={{ fontSize: 24 }} /> : 
                          <TrendingDown sx={{ fontSize: 24 }} />
                        }
                      </Box>
                      <ListItemText
                        primary={
                          <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
                            {alert.country_name}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                color: alert.direction === 'increase' 
                                  ? designTokens.colors.risk.veryHigh 
                                  : designTokens.colors.risk.low,
                                fontWeight: 500,
                                mb: 0.5,
                              }}
                            >
                              {alert.change > 0 ? '+' : ''}{alert.change.toFixed(1)} points
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(alert.current_timestamp).toLocaleDateString()} at{' '}
                              {new Date(alert.current_timestamp).toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </Typography>
                          </Box>
                        }
                      />
                    </AlertItem>
                  ))}
                </List>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </StyledContainer>
  );
};

export default Dashboard;