import { createTheme, alpha } from '@mui/material/styles';

export const brandTokens = {
  colors: {
    inkBlack: '#020617',
    voidNavy: '#041628',
    ritualCyan: '#7DFBF6',
    serumMint: '#94FADB',
    giltEdge: '#F5F26D',
    velvetPlum: '#1A0520',
    gremlinPink: '#FF8BD1',
    saintGold: '#FFCF78',
    aftercareViolet: '#9B78FF',
  },
  text: {
    primary: '#F6F7FB',
    secondary: alpha('#F6F7FB', 0.65),
  },
  gradients: {
    halo: 'radial-gradient(circle at 20% 20%, rgba(125, 251, 246, 0.25), rgba(2, 6, 23, 0.95))',
    velvet: 'linear-gradient(135deg, rgba(4, 22, 40, 0.9), rgba(26, 5, 32, 0.9))',
    focusCard: 'linear-gradient(155deg, rgba(4, 22, 40, 0.92), rgba(26, 5, 32, 0.82))',
  },
  borders: {
    cyan: alpha('#7DFBF6', 0.6),
    mint: alpha('#94FADB', 0.55),
    gold: alpha('#FFCF78', 0.7),
    subtle: alpha('#F6F7FB', 0.12),
  },
  shadows: {
    panel: '0 30px 80px rgba(4, 3, 31, 0.45)',
    goldBloom: '0 0 24px rgba(255, 207, 120, 0.2)',
  },
  surfaces: {
    chip: alpha('#041628', 0.72),
    panel: alpha('#041628', 0.5),
  },
  chips: {
    live: '[LIVE]',
    connecting: '[CONNECTING]',
    degraded: '[DEGRADED]',
    override: '[OVERRIDE]',
    blocker: '[BLOCKER]',
    aftercare: '[AFTERCARE]',
    consent: '[CONSENT CHECK? y/N]',
  },
  status: {
    low: '#94FADB',
    optimal: '#7DFBF6',
    high: '#F5F26D',
    critical: '#FF8BD1',
  },
};

export const statusStyles = {
  low: {
    color: brandTokens.status.low,
    label: 'Gentle Glide',
    border: alpha(brandTokens.status.low, 0.5),
    shadow: `0 0 24px ${alpha(brandTokens.status.low, 0.14)}`,
  },
  optimal: {
    color: brandTokens.status.optimal,
    label: 'Flow Ritual',
    border: alpha(brandTokens.status.optimal, 0.5),
    shadow: `0 0 24px ${alpha(brandTokens.status.optimal, 0.14)}`,
  },
  high: {
    color: brandTokens.status.high,
    label: 'Pressure Build',
    border: alpha(brandTokens.status.high, 0.55),
    shadow: `0 0 24px ${alpha(brandTokens.status.high, 0.18)}`,
  },
  critical: {
    color: brandTokens.status.critical,
    label: 'Break. Now.',
    border: alpha(brandTokens.status.critical, 0.55),
    shadow: `0 0 24px ${alpha(brandTokens.status.critical, 0.18)}`,
  },
} as const;

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: brandTokens.colors.ritualCyan,
    },
    secondary: {
      main: brandTokens.colors.saintGold,
    },
    background: {
      default: brandTokens.colors.inkBlack,
      paper: brandTokens.colors.voidNavy,
    },
    text: {
      primary: brandTokens.text.primary,
      secondary: brandTokens.text.secondary,
    },
    warning: {
      main: brandTokens.colors.giltEdge,
    },
    error: {
      main: brandTokens.colors.gremlinPink,
    },
  },
  typography: {
    fontFamily: '"Inter","Space Grotesk","SF Pro Display",sans-serif',
    h1: { fontSize: '2.75rem', fontWeight: 600, letterSpacing: '0.04em' },
    h2: { fontSize: '2rem', fontWeight: 600 },
    h3: { fontSize: '1.6rem', fontWeight: 500 },
    h6: { letterSpacing: '0.12em', textTransform: 'uppercase' },
    subtitle1: { fontWeight: 500 },
    button: { fontWeight: 600, letterSpacing: '0.08em' },
    fontSize: 15,
  },
  shape: {
    borderRadius: 18,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage: brandTokens.gradients.halo,
          color: '#F6F7FB',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: brandTokens.gradients.velvet,
          border: `1px solid ${alpha(brandTokens.colors.ritualCyan, 0.25)}`,
          boxShadow: brandTokens.shadows.panel,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          textTransform: 'uppercase',
          paddingInline: '1.5rem',
          backdropFilter: 'blur(8px)',
        },
        contained: {
          background: `linear-gradient(120deg, ${brandTokens.colors.ritualCyan}, ${brandTokens.colors.serumMint})`,
          color: brandTokens.colors.inkBlack,
        },
        outlined: {
          borderColor: alpha(brandTokens.colors.saintGold, 0.8),
          color: brandTokens.colors.saintGold,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontFamily: '"JetBrains Mono","IBM Plex Mono",monospace',
          borderRadius: 999,
          letterSpacing: '0.08em',
          '&:focus-visible': {
            outline: `2px solid ${brandTokens.colors.ritualCyan}`,
            outlineOffset: '2px',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: alpha('#FFFFFF', 0.1),
        },
        bar: {
          borderRadius: 6,
        },
      },
    },
  },
});

export default theme;
