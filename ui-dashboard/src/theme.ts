import { createTheme, alpha } from '@mui/material/styles';

// Direction B tokens: claudedocs/design/tokens.json and the DØPEMÜX design system
// (colors_and_type.css). Keep index.css custom properties in sync with these values.
export const brandTokens = {
  colors: {
    inkBlack: '#020617',
    voidNavy: '#041628',
    ritualCyan: '#2FFFF0',
    serumMint: '#00FF85',
    giltEdge: '#FFE600',
    velvetPlum: '#081832',
    gremlinPink: '#FF00CC',  // brand accent only — never a status indicator
    errorRed: '#FF2255',
    saintGold: '#FFC85C',
    aftercareViolet: '#C07BFF',
  },
  text: {
    primary: '#F6F7FB',
    secondary: '#94A3B8',
    muted: '#808DA0',
  },
  gradients: {
    halo: 'radial-gradient(circle at 12% 0%, rgba(47, 255, 240, 0.10), rgba(2, 6, 23, 0) 42%)',
    velvet: 'linear-gradient(135deg, rgba(4, 22, 40, 0.92), rgba(8, 24, 50, 0.92))',
    focusCard: 'linear-gradient(155deg, rgba(4, 22, 40, 0.94), rgba(8, 24, 50, 0.84))',
  },
  borders: {
    cyan: alpha('#2FFFF0', 0.6),
    mint: alpha('#00FF85', 0.55),
    gold: alpha('#FFC85C', 0.72),
    subtle: '#1E2A3A',
    strong: '#2E3F54',
  },
  shadows: {
    panel: '0 30px 80px rgba(2, 2, 24, 0.55)',
    goldBloom: '0 0 26px rgba(255, 200, 92, 0.28)',
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
    low: '#00FF85',
    optimal: '#2FFFF0',
    high: '#FFE600',
    critical: '#FF2255',
    unknown: '#808DA0',
  },
};

export function deriveStatus(load: number): 'low' | 'optimal' | 'high' | 'critical' {
  if (load > 0.8) {
    return 'critical';
  }
  if (load > 0.6) {
    return 'high';
  }
  if (load < 0.3) {
    return 'low';
  }
  return 'optimal';
}

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
  // No reading yet: grey, no glow. Never derived from a number.
  unknown: {
    color: brandTokens.status.unknown,
    label: 'Unknown',
    border: alpha(brandTokens.status.unknown, 0.5),
    shadow: 'none',
  },
} as const;

export type LoadStatus = ReturnType<typeof deriveStatus>;


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
      main: brandTokens.colors.errorRed,
    },
  },
  typography: {
    // hue.body — Inter; hue.display — Space Grotesk; hue.mono — JetBrains Mono
    fontFamily: '"Inter","SF Pro Display",sans-serif',
    h1: { fontFamily: '"Space Grotesk",sans-serif', fontSize: '2.75rem', fontWeight: 600, letterSpacing: '0.04em' },
    h2: { fontFamily: '"Space Grotesk",sans-serif', fontSize: '2rem', fontWeight: 600 },
    h3: { fontFamily: '"Space Grotesk",sans-serif', fontSize: '1.6rem', fontWeight: 500 },
    h4: { fontFamily: '"Space Grotesk",sans-serif' },
    h5: { fontFamily: '"Space Grotesk",sans-serif' },
    h6: { fontFamily: '"Space Grotesk",sans-serif', letterSpacing: '0.12em', textTransform: 'uppercase' },
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
          backgroundColor: brandTokens.colors.inkBlack,
          backgroundImage: brandTokens.gradients.halo,
          backgroundAttachment: 'fixed',
          color: brandTokens.text.primary,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: brandTokens.gradients.velvet,
          border: `1px solid ${brandTokens.borders.subtle}`,
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
          '&:focus-visible': {
            outline: `2px solid ${brandTokens.colors.ritualCyan}`,
            outlineOffset: '2px',
          },
        },
        contained: {
          background: `linear-gradient(120deg, ${brandTokens.colors.ritualCyan}, ${brandTokens.colors.serumMint})`,
          color: brandTokens.colors.inkBlack,
          '&:hover': { filter: 'brightness(1.1)' },
        },
        outlined: {
          borderColor: alpha(brandTokens.colors.saintGold, 0.8),
          color: brandTokens.colors.saintGold,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          '&:focus-visible': {
            outline: `2px solid ${brandTokens.colors.ritualCyan}`,
            outlineOffset: '2px',
          },
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
