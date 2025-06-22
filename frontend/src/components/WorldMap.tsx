import React from 'react';
import { Box, Typography } from '@mui/material';
import { Country } from '../types';

interface WorldMapProps {
  countries: Country[];
}

const WorldMap: React.FC<WorldMapProps> = ({ countries }) => {
  // This is a placeholder for the world map component
  // In a real implementation, you would use react-leaflet or similar
  
  const getRiskColor = (score: number): string => {
    if (score >= 70) return '#d32f2f';
    if (score >= 50) return '#f57c00';
    if (score >= 30) return '#fbc02d';
    return '#388e3c';
  };

  return (
    <Box 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        borderRadius: 1
      }}
    >
      <Box textAlign="center">
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Interactive World Map
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          This will display an interactive world map with countries color-coded by risk level.
          Integration with react-leaflet coming in Phase 3.
        </Typography>
        
        {/* Risk Legend */}
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
          {[
            { label: 'Low (0-30)', color: getRiskColor(20) },
            { label: 'Low-Med (30-50)', color: getRiskColor(40) },
            { label: 'Medium (50-70)', color: getRiskColor(60) },
            { label: 'High (70-100)', color: getRiskColor(80) },
          ].map((item, index) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box 
                sx={{ 
                  width: 16, 
                  height: 16, 
                  backgroundColor: item.color, 
                  borderRadius: 0.5 
                }} 
              />
              <Typography variant="caption">{item.label}</Typography>
            </Box>
          ))}
        </Box>
        
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Currently tracking {countries.length} countries
        </Typography>
      </Box>
    </Box>
  );
};

export default WorldMap;