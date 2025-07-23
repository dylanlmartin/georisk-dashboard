import React, { useState, useEffect } from 'react';
import { Box, Typography, Chip, styled, CircularProgress } from '@mui/material';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { ZoomIn, Public, Info } from '@mui/icons-material';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});
import { Country } from '../types/index.ts';
import { getRiskColor, getRiskLevel, designTokens } from '../theme/theme.ts';

// Styled components for dark theme map
const MapHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  background: `linear-gradient(135deg, ${designTokens.colors.background.secondary} 0%, ${designTokens.colors.background.tertiary} 100%)`,
  borderBottom: `1px solid ${designTokens.colors.border.subtle}`,
  borderRadius: `${designTokens.borderRadius.medium} ${designTokens.borderRadius.medium} 0 0`,
}));

const LegendContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexWrap: 'wrap',
  gap: theme.spacing(1),
  alignItems: 'center',
  marginTop: theme.spacing(2),
  padding: theme.spacing(2),
  backgroundColor: designTokens.colors.background.elevated,
  borderRadius: designTokens.borderRadius.small,
  border: `1px solid ${designTokens.colors.border.subtle}`,
}));

const LegendItem = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.5),
  padding: `${theme.spacing(0.5)} ${theme.spacing(1)}`,
  borderRadius: designTokens.borderRadius.small,
  backgroundColor: `${designTokens.colors.background.primary}80`,
  border: `1px solid ${designTokens.colors.border.subtle}`,
}));

const LegendColor = styled(Box)<{ color: string }>(({ color }) => ({
  width: 16,
  height: 16,
  backgroundColor: color,
  borderRadius: '3px',
  border: `1px solid ${designTokens.colors.border.emphasis}`,
  boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
}));

const MapContainer_Styled = styled(Box)({
  flex: 1,
  position: 'relative',
  backgroundColor: designTokens.colors.background.primary,
  minHeight: '400px', // Ensure minimum height for map
  height: '100%',
  '& .leaflet-container': {
    backgroundColor: designTokens.colors.background.primary,
    color: designTokens.colors.text.primary,
  },
  '& .leaflet-control-zoom': {
    border: `1px solid ${designTokens.colors.border.emphasis}`,
    borderRadius: designTokens.borderRadius.small,
    backgroundColor: designTokens.colors.background.elevated,
    '& a': {
      backgroundColor: designTokens.colors.background.elevated,
      color: designTokens.colors.text.primary,
      borderColor: designTokens.colors.border.emphasis,
      '&:hover': {
        backgroundColor: designTokens.colors.background.secondary,
      },
    },
  },
  '& .leaflet-popup-content-wrapper': {
    backgroundColor: designTokens.colors.background.elevated,
    color: designTokens.colors.text.primary,
    borderRadius: designTokens.borderRadius.small,
    border: `1px solid ${designTokens.colors.border.emphasis}`,
    boxShadow: designTokens.shadows.card,
  },
  '& .leaflet-popup-tip': {
    backgroundColor: designTokens.colors.background.elevated,
  },
  '& .leaflet-tooltip': {
    backgroundColor: designTokens.colors.background.elevated,
    color: designTokens.colors.text.primary,
    border: `1px solid ${designTokens.colors.border.emphasis}`,
    borderRadius: designTokens.borderRadius.small,
    fontSize: '12px',
    fontWeight: 500,
    backdropFilter: 'blur(8px)',
  },
});

const SelectedCountryPanel = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  background: `linear-gradient(135deg, ${designTokens.colors.background.tertiary} 0%, ${designTokens.colors.background.elevated} 100%)`,
  borderTop: `1px solid ${designTokens.colors.border.emphasis}`,
  borderRadius: `0 0 ${designTokens.borderRadius.medium} ${designTokens.borderRadius.medium}`,
}));

const LoadingContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  backgroundColor: designTokens.colors.background.primary,
  gap: designTokens.spacing.medium,
});

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
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setGeoData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading GeoJSON data:', error);
        setLoading(false);
      });
  }, []);
  
  const getNoDataColor = (): string => designTokens.colors.text.disabled;


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
        opacity: 0.8,
        color: designTokens.colors.border.emphasis,
        fillOpacity: 0.7
      });

      // Popup on click
      layer.on('click', () => {
        handleCountryClick(countryData);
      });

      // Hover effects
      layer.on('mouseover', () => {
        setHoveredCountry(countryData);
        layer.setStyle({
          weight: 2,
          color: designTokens.colors.accent.primary,
          fillOpacity: 0.9,
          fillColor: riskColor
        });
      });

      layer.on('mouseout', () => {
        setHoveredCountry(null);
        layer.setStyle({
          weight: 1,
          color: designTokens.colors.border.emphasis,
          fillOpacity: 0.7
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
        fillColor: getNoDataColor(),
        weight: 1,
        opacity: 0.4,
        color: designTokens.colors.border.subtle,
        fillOpacity: 0.2
      });
    }
  };


  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with legend */}
      <MapHeader>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <Public sx={{ color: designTokens.colors.accent.primary, fontSize: 28 }} />
          <Typography variant="h6" sx={{ color: designTokens.colors.text.primary, fontWeight: 600 }}>
            Interactive Geopolitical Risk Map
          </Typography>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Tracking {countries.length} countries • Click countries for details • Hover for quick info
        </Typography>
        
        {/* Risk Legend */}
        <LegendContainer>
          <Typography variant="body2" sx={{ fontWeight: 600, mr: 1, color: designTokens.colors.text.primary }}>
            Risk Level:
          </Typography>
          {[
            { label: 'Low (0-30)', score: 25 },
            { label: 'Low-Med (30-45)', score: 35 },
            { label: 'Medium (45-60)', score: 50 },
            { label: 'Med-High (60-75)', score: 65 },
            { label: 'High (75-90)', score: 80 },
            { label: 'Very High (90+)', score: 95 },
          ].map((item, index) => (
            <LegendItem key={index}>
              <LegendColor color={getRiskColor(item.score)} />
              <Typography variant="caption" sx={{ fontSize: '0.75rem', color: designTokens.colors.text.secondary }}>
                {item.label}
              </Typography>
            </LegendItem>
          ))}
          <LegendItem>
            <LegendColor color={getNoDataColor()} />
            <Typography variant="caption" sx={{ fontSize: '0.75rem', color: designTokens.colors.text.secondary }}>
              No Data
            </Typography>
          </LegendItem>
        </LegendContainer>
      </MapHeader>

      {/* Leaflet World Map */}
      <MapContainer_Styled>
        {loading ? (
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
              Loading world map...
            </Typography>
          </LoadingContainer>
        ) : geoData ? (
          <div style={{ height: '400px', width: '100%', backgroundColor: '#0D1117' }}>
            <MapContainer
              center={[20, 0]}
              zoom={1}
              minZoom={1}
              maxZoom={7}
              maxBounds={[[-90, -180], [90, 180]]}
              style={{ height: '400px', width: '100%', backgroundColor: '#0D1117' }}
              zoomControl={true}
              scrollWheelZoom={true}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                errorTileUrl="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
              />
              <GeoJSON
                data={geoData}
                onEachFeature={onEachFeature}
                key={`geojson-${countries.length}`} // Re-render when countries data changes
              />
            </MapContainer>
          </div>
        ) : (
          <LoadingContainer>
            <Typography variant="body2" color="text.secondary">
              Failed to load map data
            </Typography>
          </LoadingContainer>
        )}
      </MapContainer_Styled>

      {/* Selected Country Details */}
      {selectedCountry && (
        <SelectedCountryPanel>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Info sx={{ color: designTokens.colors.accent.primary, fontSize: 20 }} />
              <Typography variant="h6" sx={{ color: designTokens.colors.text.primary, fontWeight: 600 }}>
                {selectedCountry.name} ({selectedCountry.code})
              </Typography>
            </Box>
            {selectedCountry.latest_risk_score && (
              <Chip 
                label={`${selectedCountry.latest_risk_score.overall_score.toFixed(1)} - ${getRiskLevel(selectedCountry.latest_risk_score.overall_score)}`}
                sx={{ 
                  background: `linear-gradient(135deg, ${getRiskColor(selectedCountry.latest_risk_score.overall_score)}, ${getRiskColor(selectedCountry.latest_risk_score.overall_score)}CC)`,
                  color: 'white',
                  fontWeight: 600,
                  border: `1px solid ${getRiskColor(selectedCountry.latest_risk_score.overall_score)}40`,
                }}
              />
            )}
            <Chip 
              label={selectedCountry.region} 
              variant="outlined" 
              size="small"
              sx={{ 
                borderColor: designTokens.colors.border.emphasis,
                color: designTokens.colors.text.secondary,
              }}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Population: {selectedCountry.population.toLocaleString()}
          </Typography>
          
          {selectedCountry.latest_risk_score && (
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 2 }}>
              <Box sx={{ p: 1.5, backgroundColor: designTokens.colors.background.primary, borderRadius: 1, border: `1px solid ${designTokens.colors.border.subtle}` }}>
                <Typography variant="caption" color="text.secondary">Political</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedCountry.latest_risk_score.political_score.toFixed(1)}
                </Typography>
              </Box>
              <Box sx={{ p: 1.5, backgroundColor: designTokens.colors.background.primary, borderRadius: 1, border: `1px solid ${designTokens.colors.border.subtle}` }}>
                <Typography variant="caption" color="text.secondary">Economic</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedCountry.latest_risk_score.economic_score.toFixed(1)}
                </Typography>
              </Box>
              <Box sx={{ p: 1.5, backgroundColor: designTokens.colors.background.primary, borderRadius: 1, border: `1px solid ${designTokens.colors.border.subtle}` }}>
                <Typography variant="caption" color="text.secondary">Security</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedCountry.latest_risk_score.security_score.toFixed(1)}
                </Typography>
              </Box>
              <Box sx={{ p: 1.5, backgroundColor: designTokens.colors.background.primary, borderRadius: 1, border: `1px solid ${designTokens.colors.border.subtle}` }}>
                <Typography variant="caption" color="text.secondary">Social</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedCountry.latest_risk_score.social_score.toFixed(1)}
                </Typography>
              </Box>
              <Box sx={{ p: 1.5, backgroundColor: designTokens.colors.background.primary, borderRadius: 1, border: `1px solid ${designTokens.colors.border.subtle}` }}>
                <Typography variant="caption" color="text.secondary">Confidence</Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedCountry.latest_risk_score.confidence_level.toFixed(1)}%
                </Typography>
              </Box>
            </Box>
          )}
        </SelectedCountryPanel>
      )}
    </Box>
  );
};

export default WorldMap;