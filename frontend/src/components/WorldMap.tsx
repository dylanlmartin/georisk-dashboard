import React, { useState, useEffect } from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Country } from '../types/index.ts';

// Country name mapping for better matching between GeoJSON and our data
const countryNameMappings: { [key: string]: string } = {
  // USA variants
  'United States of America': 'United States',
  'USA': 'United States',
  'US': 'United States',
  'America': 'United States',
  
  // Other common mappings
  'Russian Federation': 'Russia',
  'Iran (Islamic Republic of)': 'Iran',
  'Syrian Arab Republic': 'Syria',
  'Yemen': 'Yemen',
  'Libya': 'Libya',
  'Myanmar': 'Myanmar',
  'Korea (Democratic People\'s Republic of)': 'North Korea',
  'Korea (Republic of)': 'South Korea',
  'Congo (Democratic Republic of the)': 'Democratic Republic of Congo',
  'Central African Republic': 'Central African Republic',
  'Bosnia and Herzegovina': 'Bosnia and Herzegovina',
  'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
  'Great Britain': 'United Kingdom',
  'Britain': 'United Kingdom',
  'UK': 'United Kingdom',
  'England': 'United Kingdom',
  'Macedonia (the former Yugoslav Republic of)': 'North Macedonia',
  'Moldova (Republic of)': 'Moldova',
  'Palestine': 'Palestine',
  'Czech Republic': 'Czech Republic',
  'Slovak Republic': 'Slovakia',
  'The Bahamas': 'Bahamas',
  'Ivory Coast': 'Ivory Coast',
  "Cote d'Ivoire": 'Ivory Coast'
};

interface WorldMapProps {
  countries: Country[];
  onCountryClick?: (country: Country) => void;
}

// Simple GeoJSON data for major countries (simplified for demo)
const worldGeoJSON = {
  "type": "FeatureCollection",
  "features": []
};

const WorldMap: React.FC<WorldMapProps> = ({ countries, onCountryClick }) => {
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<Country | null>(null);
  const [geoData, setGeoData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load world countries GeoJSON data
    fetch('https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson')
      .then(response => response.json())
      .then(data => {
        setGeoData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading GeoJSON data:', error);
        setLoading(false);
      });
  }, []);
  
  const getRiskColor = (score?: number): string => {
    if (!score) return '#e0e0e0'; // Gray for no data
    if (score >= 70) return '#d32f2f'; // Red - Very High Risk
    if (score >= 60) return '#f44336'; // Red-Orange - High Risk
    if (score >= 50) return '#ff9800'; // Orange - Medium-High Risk
    if (score >= 40) return '#ffc107'; // Amber - Medium Risk
    if (score >= 30) return '#ffeb3b'; // Yellow - Low-Medium Risk
    return '#4caf50'; // Green - Low Risk
  };

  const getRiskLevel = (score?: number): string => {
    if (!score) return 'No Data';
    if (score >= 70) return 'Very High Risk';
    if (score >= 60) return 'High Risk';
    if (score >= 50) return 'Medium-High Risk';
    if (score >= 40) return 'Medium Risk';
    if (score >= 30) return 'Low-Medium Risk';
    return 'Low Risk';
  };


  const handleCountryHover = (country: Country) => {
    setHoveredCountry(country);
  };

  const handleCountryClick = (country: Country) => {
    setSelectedCountry(country);
    if (onCountryClick) {
      onCountryClick(country);
    }
  };

  const getCountryData = (countryName: string): Country | undefined => {
    if (!countryName) return undefined;
    
    // Check if there's a direct mapping for this country name
    const mappedName = countryNameMappings[countryName] || countryName;
    
    // Try exact matches first
    let match = countries.find(c => 
      c.name.toLowerCase() === mappedName.toLowerCase() ||
      c.name.toLowerCase() === countryName.toLowerCase() ||
      c.code.toLowerCase() === countryName.toLowerCase()
    );
    
    // If no exact match, try partial matching for common variations
    if (!match) {
      match = countries.find(c => {
        const cNameLower = c.name.toLowerCase();
        const searchLower = countryName.toLowerCase();
        const mappedLower = mappedName.toLowerCase();
        
        // Check if country name contains search term or vice versa
        return cNameLower.includes(searchLower) || 
               searchLower.includes(cNameLower) ||
               cNameLower.includes(mappedLower) ||
               mappedLower.includes(cNameLower);
      });
    }
    
    return match;
  };

  const onEachFeature = (feature: any, layer: any) => {
    const countryName = feature.properties.name || feature.properties.NAME || feature.properties.NAME_EN;
    const countryData = getCountryData(countryName);
    
    
    if (countryData) {
      const riskScore = countryData.latest_risk_score?.overall_score;
      const riskColor = getRiskColor(riskScore);
      
      layer.setStyle({
        fillColor: riskColor,
        weight: 1,
        opacity: 0.7,
        color: '#666',
        fillOpacity: 0.8
      });

      // Popup on click
      layer.on('click', () => {
        handleCountryClick(countryData);
      });

      // Hover effects
      layer.on('mouseover', () => {
        setHoveredCountry(countryData);
        layer.setStyle({
          weight: 3,
          color: '#333',
          fillOpacity: 1.0
        });
      });

      layer.on('mouseout', () => {
        setHoveredCountry(null);
        layer.setStyle({
          weight: 1,
          color: '#666',
          fillOpacity: 0.8
        });
      });

      // Tooltip
      layer.bindTooltip(`
        <strong>${countryData.name}</strong><br/>
        Risk Score: ${riskScore ? riskScore.toFixed(1) : 'No Data'}<br/>
        Level: ${getRiskLevel(riskScore)}<br/>
        Region: ${countryData.region}
      `, {
        permanent: false,
        direction: 'top'
      });
    } else {
      // Style for countries not in our dataset
      layer.setStyle({
        fillColor: '#f0f0f0',
        weight: 1,
        opacity: 0.5,
        color: '#ccc',
        fillOpacity: 0.3
      });
    }
  };


  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with legend */}
      <Box sx={{ p: 2, backgroundColor: '#f8f9fa', borderRadius: '8px 8px 0 0' }}>
        <Typography variant="h6" gutterBottom sx={{ color: '#1976d2', fontWeight: 600 }}>
          Interactive Geopolitical Risk Map
        </Typography>
        
        {/* Risk Legend */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
          <Typography variant="body2" sx={{ fontWeight: 500, mr: 1 }}>Risk Level:</Typography>
          {[
            { label: 'Low (0-30)', score: 25 },
            { label: 'Low-Med (30-40)', score: 35 },
            { label: 'Medium (40-50)', score: 45 },
            { label: 'Med-High (50-60)', score: 55 },
            { label: 'High (60-70)', score: 65 },
            { label: 'Very High (70+)', score: 75 },
          ].map((item, index) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box 
                sx={{ 
                  width: 14, 
                  height: 14, 
                  backgroundColor: getRiskColor(item.score), 
                  borderRadius: '2px',
                  border: '1px solid rgba(0,0,0,0.1)'
                }} 
              />
              <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#666' }}>
                {item.label}
              </Typography>
            </Box>
          ))}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
            <Box 
              sx={{ 
                width: 14, 
                height: 14, 
                backgroundColor: '#e0e0e0', 
                borderRadius: '2px',
                border: '1px solid rgba(0,0,0,0.1)'
              }} 
            />
            <Typography variant="caption" sx={{ fontSize: '0.7rem', color: '#666' }}>
              No Data
            </Typography>
          </Box>
        </Box>
        
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Tracking {countries.length} countries • Click countries on map for details • Hover for quick info
        </Typography>
      </Box>

      {/* Leaflet World Map */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        {loading ? (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            backgroundColor: '#f5f7fa'
          }}>
            <Typography variant="body2" color="text.secondary">
              Loading world map...
            </Typography>
          </Box>
        ) : geoData ? (
          <MapContainer
            center={[20, 0]}
            zoom={2}
            style={{ height: '100%', width: '100%' }}
            zoomControl={true}
            scrollWheelZoom={true}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <GeoJSON
              data={geoData}
              onEachFeature={onEachFeature}
              key={`geojson-${countries.length}`} // Re-render when countries data changes
            />
          </MapContainer>
        ) : (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            backgroundColor: '#f5f7fa'
          }}>
            <Typography variant="body2" color="text.secondary">
              Failed to load map data
            </Typography>
          </Box>
        )}
      </Box>

      {/* Selected Country Details */}
      {selectedCountry && (
        <Box sx={{ p: 2, backgroundColor: '#ffffff', borderTop: '1px solid #e0e0e0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Typography variant="h6" sx={{ color: '#1976d2' }}>
              {selectedCountry.name} ({selectedCountry.code})
            </Typography>
            {selectedCountry.latest_risk_score && (
              <Chip 
                label={`Risk: ${selectedCountry.latest_risk_score.overall_score.toFixed(1)} - ${getRiskLevel(selectedCountry.latest_risk_score.overall_score)}`}
                sx={{ 
                  backgroundColor: getRiskColor(selectedCountry.latest_risk_score.overall_score),
                  color: selectedCountry.latest_risk_score.overall_score > 50 ? 'white' : 'black',
                  fontWeight: 600
                }}
              />
            )}
            <Chip label={selectedCountry.region} variant="outlined" size="small" />
            <Typography variant="body2" color="text.secondary">
              Population: {selectedCountry.population.toLocaleString()}
            </Typography>
          </Box>
          
          {selectedCountry.latest_risk_score && (
            <Box sx={{ mt: 1, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Typography variant="body2">
                Political: <strong>{selectedCountry.latest_risk_score.political_score.toFixed(1)}</strong>
              </Typography>
              <Typography variant="body2">
                Economic: <strong>{selectedCountry.latest_risk_score.economic_score.toFixed(1)}</strong>
              </Typography>
              <Typography variant="body2">
                Security: <strong>{selectedCountry.latest_risk_score.security_score.toFixed(1)}</strong>
              </Typography>
              <Typography variant="body2">
                Social: <strong>{selectedCountry.latest_risk_score.social_score.toFixed(1)}</strong>
              </Typography>
              <Typography variant="body2">
                Confidence: <strong>{selectedCountry.latest_risk_score.confidence_level.toFixed(1)}%</strong>
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default WorldMap;