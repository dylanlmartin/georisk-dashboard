import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Box, Typography, CircularProgress } from '@mui/material';
import apiService from '../services/api';

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
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (trendData.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography color="text.secondary">
          No trend data available yet. Data will appear after risk scores are calculated.
        </Typography>
      </Box>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="90%">
      <LineChart data={trendData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="overall" 
          stroke="#1976d2" 
          strokeWidth={3}
          name="Overall Risk" 
        />
        <Line 
          type="monotone" 
          dataKey="political" 
          stroke="#9c27b0" 
          name="Political" 
        />
        <Line 
          type="monotone" 
          dataKey="economic" 
          stroke="#f57c00" 
          name="Economic" 
        />
        <Line 
          type="monotone" 
          dataKey="security" 
          stroke="#d32f2f" 
          name="Security" 
        />
        <Line 
          type="monotone" 
          dataKey="social" 
          stroke="#388e3c" 
          name="Social" 
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default RiskChart;