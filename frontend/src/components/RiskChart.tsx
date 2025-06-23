import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Box, Typography, CircularProgress, styled } from '@mui/material';
import { TrendingUp } from '@mui/icons-material';
import apiService from '../services/api.ts';
import { designTokens } from '../theme/theme.ts';

// Styled components for modern chart design
const LoadingContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  gap: designTokens.spacing.medium,
});

const EmptyStateContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  textAlign: 'center',
  color: designTokens.colors.text.secondary,
});

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <Box
        sx={{
          backgroundColor: designTokens.colors.background.elevated,
          border: `1px solid ${designTokens.colors.border.emphasis}`,
          borderRadius: designTokens.borderRadius.small,
          padding: 2,
          backdropFilter: 'blur(8px)',
          boxShadow: designTokens.shadows.card,
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
          {label}
        </Typography>
        {payload.map((entry: any, index: number) => (
          <Typography
            key={index}
            variant="caption"
            sx={{
              color: entry.color,
              display: 'block',
              fontWeight: 500,
            }}
          >
            {entry.name}: {entry.value.toFixed(1)}
          </Typography>
        ))}
      </Box>
    );
  }
  return null;
};

// Chart color scheme based on design tokens
const chartColors = {
  overall: designTokens.colors.accent.primary,
  political: designTokens.colors.risk.medium,
  economic: designTokens.colors.risk.mediumHigh,
  security: designTokens.colors.risk.veryHigh,
  social: designTokens.colors.risk.low,
};

const RiskChart: React.FC = () => {
  const [trendData, setTrendData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrendData();
  }, []);

  const loadTrendData = async () => {
    try {
      const data = await apiService.getRiskTrends(7);
      const formattedData = data.trends.map((trend: any) => ({
        date: new Date(trend.date).toLocaleDateString(),
        overall: trend.average_overall_score,
        political: trend.average_political_score,
        economic: trend.average_economic_score,
        security: trend.average_security_score,
        social: trend.average_social_score,
      }));
      setTrendData(formattedData);
    } catch (error) {
      console.error('Error loading trend data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <LoadingContainer>
        <CircularProgress 
          size={48} 
          sx={{ 
            color: designTokens.colors.accent.primary,
            '& .MuiCircularProgress-circle': {
              strokeLinecap: 'round',
            },
          }} 
        />
        <Typography variant="body2" color="text.secondary">
          Loading trend data...
        </Typography>
      </LoadingContainer>
    );
  }

  if (trendData.length === 0) {
    return (
      <EmptyStateContainer>
        <TrendingUp sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
        <Typography variant="h6" sx={{ mb: 1 }}>
          No trend data available
        </Typography>
        <Typography variant="body2" sx={{ maxWidth: 300 }}>
          Historical trends will appear here once sufficient risk score data has been collected over time.
        </Typography>
      </EmptyStateContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart 
        data={trendData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid 
          strokeDasharray="3 3" 
          stroke={designTokens.colors.border.subtle}
          strokeOpacity={0.5}
        />
        <XAxis 
          dataKey="date" 
          tick={{ 
            fill: designTokens.colors.text.secondary, 
            fontSize: 12 
          }}
          tickLine={{ stroke: designTokens.colors.border.emphasis }}
          axisLine={{ stroke: designTokens.colors.border.emphasis }}
        />
        <YAxis 
          domain={[0, 100]}
          tick={{ 
            fill: designTokens.colors.text.secondary, 
            fontSize: 12 
          }}
          tickLine={{ stroke: designTokens.colors.border.emphasis }}
          axisLine={{ stroke: designTokens.colors.border.emphasis }}
          label={{ 
            value: 'Risk Score', 
            angle: -90, 
            position: 'insideLeft',
            style: { 
              textAnchor: 'middle',
              fill: designTokens.colors.text.secondary,
              fontSize: '12px'
            }
          }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          wrapperStyle={{ 
            fontSize: '12px',
            color: designTokens.colors.text.secondary,
            paddingTop: '16px'
          }}
          iconSize={12}
          height={40}
        />
        <Line 
          type="monotone" 
          dataKey="overall" 
          stroke={chartColors.overall}
          strokeWidth={3}
          name="Overall Risk"
          dot={{ fill: chartColors.overall, strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: chartColors.overall, strokeWidth: 2 }}
        />
        <Line 
          type="monotone" 
          dataKey="political" 
          stroke={chartColors.political}
          strokeWidth={2}
          name="Political"
          dot={{ fill: chartColors.political, strokeWidth: 1, r: 3 }}
          activeDot={{ r: 5, stroke: chartColors.political, strokeWidth: 2 }}
        />
        <Line 
          type="monotone" 
          dataKey="economic" 
          stroke={chartColors.economic}
          strokeWidth={2}
          name="Economic"
          dot={{ fill: chartColors.economic, strokeWidth: 1, r: 3 }}
          activeDot={{ r: 5, stroke: chartColors.economic, strokeWidth: 2 }}
        />
        <Line 
          type="monotone" 
          dataKey="security" 
          stroke={chartColors.security}
          strokeWidth={2}
          name="Security"
          dot={{ fill: chartColors.security, strokeWidth: 1, r: 3 }}
          activeDot={{ r: 5, stroke: chartColors.security, strokeWidth: 2 }}
        />
        <Line 
          type="monotone" 
          dataKey="social" 
          stroke={chartColors.social}
          strokeWidth={2}
          name="Social"
          dot={{ fill: chartColors.social, strokeWidth: 1, r: 3 }}
          activeDot={{ r: 5, stroke: chartColors.social, strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default RiskChart;