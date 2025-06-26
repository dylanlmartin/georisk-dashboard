import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Chip,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Divider,
  styled,
  Slide,
  Paper,
} from '@mui/material';
import {
  Close,
  Public,
  People,
  TrendingUp,
  Security,
  AccountBalance,
  Gavel,
  Groups,
  Info,
  AutoAwesome,
} from '@mui/icons-material';
import { Country } from '../types/index.ts';
import { getRiskColor, getRiskLevel, designTokens } from '../theme/theme.ts';
import apiService from '../services/api.ts';

interface CountryDetailWidgetProps {
  country: Country | null;
  isOpen: boolean;
  onClose: () => void;
}

// Styled components
const WidgetContainer = styled(Paper)(({ theme }) => ({
  position: 'fixed',
  top: 0,
  right: 0,
  width: '480px',
  height: '100vh',
  background: `linear-gradient(180deg, ${designTokens.colors.background.secondary} 0%, ${designTokens.colors.background.primary} 100%)`,
  border: `1px solid ${designTokens.colors.border.emphasis}`,
  borderRight: 'none',
  borderRadius: `${designTokens.borderRadius.large} 0 0 ${designTokens.borderRadius.large}`,
  boxShadow: '0 0 32px rgba(0, 0, 0, 0.5)',
  zIndex: 1300,
  display: 'flex',
  flexDirection: 'column',
  backdropFilter: 'blur(10px)',
  overflow: 'hidden',
  '@media (max-width: 768px)': {
    width: '100vw',
    borderRadius: 0,
  },
}));

const Header = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  background: `linear-gradient(135deg, ${designTokens.colors.background.tertiary} 0%, ${designTokens.colors.background.elevated} 100%)`,
  borderBottom: `1px solid ${designTokens.colors.border.emphasis}`,
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `radial-gradient(circle at top right, ${designTokens.colors.accent.primary}15 0%, transparent 50%)`,
    pointerEvents: 'none',
  },
}));

const ContentArea = styled(Box)({
  flex: 1,
  overflow: 'auto',
  padding: designTokens.spacing.large,
  '&::-webkit-scrollbar': {
    width: '6px',
  },
  '&::-webkit-scrollbar-track': {
    background: designTokens.colors.background.secondary,
  },
  '&::-webkit-scrollbar-thumb': {
    background: designTokens.colors.border.emphasis,
    borderRadius: '3px',
  },
});

const MetricCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(135deg, ${designTokens.colors.background.elevated} 0%, ${designTokens.colors.background.tertiary} 100%)`,
  border: `1px solid ${designTokens.colors.border.subtle}`,
  borderRadius: designTokens.borderRadius.medium,
  transition: 'all 0.2s ease-out',
  '&:hover': {
    transform: 'translateY(-2px)',
    borderColor: designTokens.colors.border.emphasis,
    boxShadow: designTokens.shadows.cardHover,
  },
}));

const RiskScoreChip = styled(Chip)<{ score: number }>(({ score }) => ({
  background: `linear-gradient(135deg, ${getRiskColor(score)}, ${getRiskColor(score)}CC)`,
  color: 'white',
  fontWeight: 600,
  fontSize: '1rem',
  height: '40px',
  border: `1px solid ${getRiskColor(score)}40`,
  '& .MuiChip-label': {
    padding: '0 16px',
  },
}));

const AnalysisCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(135deg, ${designTokens.colors.background.elevated} 0%, ${designTokens.colors.background.tertiary} 100%)`,
  border: `1px solid ${designTokens.colors.border.emphasis}`,
  borderRadius: designTokens.borderRadius.medium,
  marginTop: theme.spacing(3),
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
    background: `linear-gradient(90deg, ${designTokens.colors.accent.primary}, ${designTokens.colors.accent.hover})`,
  },
}));

const LoadingContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: designTokens.spacing.xlarge,
  gap: designTokens.spacing.medium,
});

interface CountryAnalysis {
  summary: string;
  key_drivers: string[];
  risk_factors: string[];
  stability_factors: string[];
  outlook: string;
}

const CountryDetailWidget: React.FC<CountryDetailWidgetProps> = ({
  country,
  isOpen,
  onClose,
}) => {
  const [analysis, setAnalysis] = useState<CountryAnalysis | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    if (country && isOpen) {
      loadCountryAnalysis();
    }
  }, [country, isOpen]);

  const loadCountryAnalysis = async () => {
    if (!country) return;
    
    setLoadingAnalysis(true);
    try {
      const analysisData = await apiService.getCountryAnalysis(country.code);
      setAnalysis(analysisData);
    } catch (error) {
      console.error('Error loading country analysis:', error);
      setAnalysis({
        summary: `Unable to load detailed analysis for ${country.name}. Basic risk assessment shows an overall score of ${country.latest_risk_score?.overall_score?.toFixed(1) || 'N/A'}.`,
        key_drivers: ['Analysis temporarily unavailable'],
        risk_factors: ['Unable to assess current risk factors'],
        stability_factors: ['Unable to assess stability factors'],
        outlook: 'Detailed analysis will be available when data connection is restored.'
      });
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const formatPopulation = (population: number): string => {
    if (population >= 1000000000) {
      return `${(population / 1000000000).toFixed(1)}B`;
    } else if (population >= 1000000) {
      return `${(population / 1000000).toFixed(1)}M`;
    } else if (population >= 1000) {
      return `${(population / 1000).toFixed(0)}K`;
    }
    return population.toString();
  };

  if (!country) return null;

  return (
    <Slide direction="left" in={isOpen} mountOnEnter unmountOnExit>
      <WidgetContainer elevation={24}>
        {/* Header */}
        <Header>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', position: 'relative', zIndex: 1 }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Public sx={{ color: designTokens.colors.accent.primary, fontSize: 28 }} />
                <Typography variant="h4" sx={{ fontWeight: 700, color: designTokens.colors.text.primary }}>
                  {country.name}
                </Typography>
              </Box>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                {country.region} • Population: {formatPopulation(country.population)}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip 
                  label={country.code} 
                  variant="outlined" 
                  size="small"
                  sx={{ 
                    borderColor: designTokens.colors.border.emphasis,
                    color: designTokens.colors.text.secondary,
                  }}
                />
                {country.latest_risk_score && (
                  <RiskScoreChip
                    label={`${country.latest_risk_score.overall_score.toFixed(1)} - ${getRiskLevel(country.latest_risk_score.overall_score)}`}
                    score={country.latest_risk_score.overall_score}
                  />
                )}
              </Box>
            </Box>
            <IconButton
              onClick={onClose}
              sx={{
                color: designTokens.colors.text.secondary,
                backgroundColor: `${designTokens.colors.background.elevated}80`,
                backdropFilter: 'blur(8px)',
                '&:hover': {
                  backgroundColor: designTokens.colors.background.elevated,
                  color: designTokens.colors.text.primary,
                },
              }}
            >
              <Close />
            </IconButton>
          </Box>
        </Header>

        {/* Content */}
        <ContentArea>
          {/* Risk Metrics Grid */}
          {country.latest_risk_score && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp sx={{ color: designTokens.colors.accent.primary }} />
                Risk Score Breakdown
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <MetricCard>
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Gavel sx={{ color: designTokens.colors.risk.medium, fontSize: 20 }} />
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                          Political
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {country.latest_risk_score.political_score.toFixed(1)}
                      </Typography>
                    </CardContent>
                  </MetricCard>
                </Grid>
                <Grid item xs={6}>
                  <MetricCard>
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <AccountBalance sx={{ color: designTokens.colors.risk.mediumHigh, fontSize: 20 }} />
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                          Economic
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {country.latest_risk_score.economic_score.toFixed(1)}
                      </Typography>
                    </CardContent>
                  </MetricCard>
                </Grid>
                <Grid item xs={6}>
                  <MetricCard>
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Security sx={{ color: designTokens.colors.risk.veryHigh, fontSize: 20 }} />
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                          Security
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {country.latest_risk_score.security_score.toFixed(1)}
                      </Typography>
                    </CardContent>
                  </MetricCard>
                </Grid>
                <Grid item xs={6}>
                  <MetricCard>
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Groups sx={{ color: designTokens.colors.risk.low, fontSize: 20 }} />
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                          Social
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {country.latest_risk_score.social_score.toFixed(1)}
                      </Typography>
                    </CardContent>
                  </MetricCard>
                </Grid>
              </Grid>
              
              <MetricCard sx={{ mt: 2 }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Info sx={{ color: designTokens.colors.accent.primary, fontSize: 20 }} />
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                        Confidence Level
                      </Typography>
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {country.latest_risk_score.confidence_level.toFixed(1)}%
                    </Typography>
                  </Box>
                </CardContent>
              </MetricCard>
            </Box>
          )}

          {/* AI Analysis Section */}
          <AnalysisCard>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <AutoAwesome sx={{ color: designTokens.colors.accent.primary }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  AI Risk Analysis
                </Typography>
              </Box>

              {loadingAnalysis ? (
                <LoadingContainer>
                  <CircularProgress 
                    size={40} 
                    sx={{ color: designTokens.colors.accent.primary }} 
                  />
                  <Typography variant="body2" color="text.secondary">
                    Generating risk analysis...
                  </Typography>
                </LoadingContainer>
              ) : analysis ? (
                <Box>
                  {/* Summary */}
                  <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.6 }}>
                    {analysis.summary}
                  </Typography>

                  <Divider sx={{ my: 2, borderColor: designTokens.colors.border.subtle }} />

                  {/* Key Drivers */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: '0.9rem' }}>
                      Key Risk Drivers
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {analysis.key_drivers.map((driver, index) => (
                        <Typography key={index} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Box sx={{ 
                            width: 4, 
                            height: 4, 
                            backgroundColor: designTokens.colors.accent.primary, 
                            borderRadius: '50%', 
                            mt: 1,
                            flexShrink: 0,
                          }} />
                          {driver}
                        </Typography>
                      ))}
                    </Box>
                  </Box>

                  {/* Risk Factors */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: '0.9rem', color: designTokens.colors.risk.high }}>
                      Risk Factors
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {analysis.risk_factors.map((factor, index) => (
                        <Typography key={index} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Box sx={{ 
                            width: 4, 
                            height: 4, 
                            backgroundColor: designTokens.colors.risk.high, 
                            borderRadius: '50%', 
                            mt: 1,
                            flexShrink: 0,
                          }} />
                          {factor}
                        </Typography>
                      ))}
                    </Box>
                  </Box>

                  {/* Stability Factors */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: '0.9rem', color: designTokens.colors.risk.low }}>
                      Stability Factors
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {analysis.stability_factors.map((factor, index) => (
                        <Typography key={index} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Box sx={{ 
                            width: 4, 
                            height: 4, 
                            backgroundColor: designTokens.colors.risk.low, 
                            borderRadius: '50%', 
                            mt: 1,
                            flexShrink: 0,
                          }} />
                          {factor}
                        </Typography>
                      ))}
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2, borderColor: designTokens.colors.border.subtle }} />

                  {/* Outlook */}
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: '0.9rem' }}>
                      Outlook
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic', color: designTokens.colors.text.secondary }}>
                      {analysis.outlook}
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Unable to load risk analysis at this time.
                </Typography>
              )}
            </CardContent>
          </AnalysisCard>
        </ContentArea>
      </WidgetContainer>
    </Slide>
  );
};

export default CountryDetailWidget;