import { createTheme, ThemeOptions } from '@mui/material/styles';

// Design tokens based on specification
const designTokens = {
  colors: {
    background: {
      primary: '#0D1117',
      secondary: '#161B22', 
      tertiary: '#21262D',
      elevated: '#30363D',
    },
    border: {
      subtle: '#21262D',
      emphasis: '#30363D',
      active: '#F85149',
    },
    risk: {
      veryHigh: '#FF4444',
      high: '#FF6B35',
      mediumHigh: '#FF8500',
      medium: '#FFB800',
      lowMedium: '#FFDD00',
      low: '#00DD88',
    },
    accent: {
      primary: '#58A6FF',
      secondary: '#1F6FEB',
      hover: '#388BFD',
    },
    text: {
      primary: '#F0F6FC',
      secondary: '#8B949E',
      tertiary: '#6E7681',
      disabled: '#484F58',
    },
    status: {
      success: '#238636',
      warning: '#9A6700',
      error: '#DA3633',
      info: '#0969DA',
    }
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontFamilyMono: "'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace",
  },
  spacing: {
    micro: '4px',
    small: '8px',
    medium: '16px',
    large: '24px',
    xlarge: '32px',
    xxlarge: '48px',
    huge: '64px',
  },
  borderRadius: {
    small: '6px',
    medium: '12px',
    large: '16px',
    round: '50%',
  },
  shadows: {
    card: '0 4px 12px rgba(0, 0, 0, 0.3)',
    cardHover: '0 8px 24px rgba(0, 0, 0, 0.4)',
    focus: '0 0 0 2px #58A6FF',
  }
};

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: {
      main: designTokens.colors.accent.primary,
      dark: designTokens.colors.accent.secondary,
      light: designTokens.colors.accent.hover,
    },
    secondary: {
      main: designTokens.colors.risk.medium,
      dark: designTokens.colors.risk.high,
      light: designTokens.colors.risk.lowMedium,
    },
    background: {
      default: designTokens.colors.background.primary,
      paper: designTokens.colors.background.tertiary,
    },
    text: {
      primary: designTokens.colors.text.primary,
      secondary: designTokens.colors.text.secondary,
      disabled: designTokens.colors.text.disabled,
    },
    divider: designTokens.colors.border.subtle,
    error: {
      main: designTokens.colors.status.error,
    },
    warning: {
      main: designTokens.colors.status.warning,
    },
    info: {
      main: designTokens.colors.status.info,
    },
    success: {
      main: designTokens.colors.status.success,
    },
  },
  typography: {
    fontFamily: designTokens.typography.fontFamily,
    h1: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.5px',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '1.5rem',
      fontWeight: 600,
      letterSpacing: '-0.25px',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '0.875rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.4,
    },
    caption: {
      fontSize: '0.6875rem',
      lineHeight: 1.3,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: designTokens.colors.background.primary,
          color: designTokens.colors.text.primary,
          fontFamily: designTokens.typography.fontFamily,
        },
        '*': {
          boxSizing: 'border-box',
        },
        '*::-webkit-scrollbar': {
          width: '8px',
        },
        '*::-webkit-scrollbar-track': {
          background: designTokens.colors.background.secondary,
        },
        '*::-webkit-scrollbar-thumb': {
          background: designTokens.colors.border.emphasis,
          borderRadius: '4px',
        },
        '*::-webkit-scrollbar-thumb:hover': {
          background: designTokens.colors.text.tertiary,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: designTokens.colors.background.tertiary,
          backgroundImage: 'none',
          border: `1px solid ${designTokens.colors.border.subtle}`,
          borderRadius: designTokens.borderRadius.medium,
          boxShadow: designTokens.shadows.card,
          transition: 'box-shadow 0.2s ease-out',
          '&:hover': {
            boxShadow: designTokens.shadows.cardHover,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: designTokens.colors.background.tertiary,
          border: `1px solid ${designTokens.colors.border.subtle}`,
          borderRadius: designTokens.borderRadius.medium,
          boxShadow: designTokens.shadows.card,
          transition: 'all 0.2s ease-out',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: designTokens.shadows.cardHover,
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius.small,
          textTransform: 'none',
          fontWeight: 500,
          transition: 'all 0.15s ease-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'scale(0.98)',
          },
        },
        contained: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius.small,
          fontWeight: 500,
        },
      },
    },
    MuiListItem: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius.small,
          marginBottom: designTokens.spacing.small,
          transition: 'background-color 0.15s ease-out',
          '&:hover': {
            backgroundColor: designTokens.colors.background.elevated,
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: designTokens.colors.background.elevated,
          border: `1px solid ${designTokens.colors.border.emphasis}`,
          borderRadius: designTokens.borderRadius.small,
          backdropFilter: 'blur(8px)',
          fontSize: '0.75rem',
        },
      },
    },
  },
};

export const theme = createTheme(themeOptions);
export { designTokens };

// Risk level utilities
export const getRiskColor = (score: number): string => {
  if (score >= 90) return designTokens.colors.risk.veryHigh;
  if (score >= 75) return designTokens.colors.risk.high;
  if (score >= 60) return designTokens.colors.risk.mediumHigh;
  if (score >= 45) return designTokens.colors.risk.medium;
  if (score >= 30) return designTokens.colors.risk.lowMedium;
  return designTokens.colors.risk.low;
};

export const getRiskGradient = (score: number): string => {
  const color = getRiskColor(score);
  const darkerShade = color.replace('#', '#').slice(0, 7) + '80'; // Add transparency
  return `linear-gradient(135deg, ${color}, ${darkerShade})`;
};

export const getRiskLevel = (score: number): string => {
  if (score >= 90) return 'Very High';
  if (score >= 75) return 'High';
  if (score >= 60) return 'Medium-High';
  if (score >= 45) return 'Medium';
  if (score >= 30) return 'Low-Medium';
  return 'Low';
};