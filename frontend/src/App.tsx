import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Dashboard from './components/Dashboard.tsx';
import CountryDetail from './components/CountryDetail.tsx';
import { theme } from './theme/theme.ts';
import 'leaflet/dist/leaflet.css';

// Import Inter font
const fontLink = document.createElement('link');
fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
fontLink.rel = 'stylesheet';
document.head.appendChild(fontLink);

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/country/:countryCode" element={<CountryDetail />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;