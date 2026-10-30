import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';

import { brandTokens, deriveStatus, statusStyles } from '../theme';

interface LoadInstrumentProps {
  /** Current cognitive load, 0..1. `null` means no reading, which renders as unknown. */
  load: number | null;
  /** Backend 15-minute forecast, 0..1. `null` when the backend sends none. */
  prediction: number | null;
  recommendation: string | null;
}

// Zone widths mirror deriveStatus: <30 low, 30-60 optimal, 60-80 high, >80 critical.
const ZONES = [
  { status: 'low', label: 'GLIDE', width: 30 },
  { status: 'optimal', label: 'FLOW', width: 30 },
  { status: 'high', label: 'PRESSURE', width: 20 },
  { status: 'critical', label: 'BREAK', width: 20 },
] as const;

const STATE_HINTS: Record<keyof typeof statusStyles, string> = {
  low: 'Low load. Good time for a hard task.',
  optimal: 'Load in range. Keep going.',
  high: 'Load rising. Plan a break.',
  critical: 'Load critical. Stop and step away.',
};

const eyebrowSx = {
  fontFamily: '"JetBrains Mono", monospace',
  fontSize: '0.75rem',
  fontWeight: 600,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: brandTokens.text.secondary,
} as const;

const toPercent = (value: number) => Math.round(value * 100);

const LoadInstrument: React.FC<LoadInstrumentProps> = ({ load, prediction, recommendation }) => {
  const status = load === null ? null : deriveStatus(load);
  const stateColor = status ? statusStyles[status].color : brandTokens.status.unknown;
  const loadPercent = load === null ? null : toPercent(load);
  const forecastPercent = prediction === null ? null : toPercent(prediction);
  const forecastDelta =
    loadPercent !== null && forecastPercent !== null ? forecastPercent - loadPercent : null;

  const valueText =
    loadPercent !== null && status
      ? `${loadPercent}%, ${statusStyles[status].label}` +
        (forecastPercent !== null ? `, forecast ${forecastPercent}% in 15 minutes` : '')
      : undefined;

  return (
    <Paper
      component="section"
      aria-labelledby="load-instrument-title"
      sx={{
        p: 3,
        borderRadius: '18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 2.5,
        background: brandTokens.gradients.focusCard,
        borderColor: status ? alpha(stateColor, 0.5) : brandTokens.borders.subtle,
        boxShadow: status ? `0 0 28px ${alpha(stateColor, 0.16)}` : 'none',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 1.5 }}>
        <Typography id="load-instrument-title" component="h2" sx={eyebrowSx}>
          Cognitive Load
        </Typography>
        <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', color: brandTokens.text.muted }}>
          source adhd-engine
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 2, flexWrap: 'wrap' }}>
        <Typography
          component="span"
          sx={{
            fontFamily: '"Space Grotesk", sans-serif',
            fontWeight: 600,
            fontSize: { xs: '4.5rem', md: '5.5rem' },
            lineHeight: 0.9,
            letterSpacing: '-0.02em',
            color: stateColor,
          }}
        >
          {loadPercent !== null ? `${loadPercent}%` : '—'}
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, pb: 0.75 }}>
          <Typography
            component="span"
            sx={{
              fontFamily: status ? '"Space Grotesk", sans-serif' : '"JetBrains Mono", monospace',
              fontWeight: 600,
              fontSize: status ? '1.5rem' : '1.25rem',
              letterSpacing: status ? 0 : '0.08em',
              color: stateColor,
            }}
          >
            {status ? statusStyles[status].label : 'Unknown'}
          </Typography>
          <Typography component="span" sx={{ fontSize: '0.875rem', color: brandTokens.text.secondary }}>
            {status ? STATE_HINTS[status] : 'No reading received.'}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, opacity: status ? 1 : 0.45 }}>
        <Box
          {...(status
            ? {
                role: 'meter',
                'aria-label': 'Cognitive load',
                'aria-valuemin': 0,
                'aria-valuemax': 100,
                'aria-valuenow': loadPercent ?? undefined,
                'aria-valuetext': valueText,
              }
            : { 'aria-hidden': true })}
          sx={{ position: 'relative', height: 44 }}
        >
          <Box
            aria-hidden="true"
            sx={{ position: 'absolute', left: 0, right: 0, top: 16, height: 14, display: 'flex', borderRadius: '7px', overflow: 'hidden' }}
          >
            {ZONES.map((zone) => (
              <Box
                key={zone.status}
                sx={{
                  width: `${zone.width}%`,
                  bgcolor: status ? alpha(statusStyles[zone.status].color, 0.24) : alpha(brandTokens.status.unknown, 0.22),
                }}
              />
            ))}
          </Box>
          {status && forecastPercent !== null && (
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                top: 10,
                left: `${forecastPercent}%`,
                height: 26,
                borderLeft: `2px dashed ${brandTokens.text.secondary}`,
                transition: 'left 0.6s ease',
              }}
            />
          )}
          {status && loadPercent !== null && (
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                top: 0,
                left: `${loadPercent}%`,
                transform: 'translateX(-50%)',
                width: 4,
                height: 44,
                borderRadius: '2px',
                bgcolor: brandTokens.text.primary,
                boxShadow: `0 0 10px ${alpha(brandTokens.text.primary, 0.6)}`,
                transition: 'left 0.6s ease',
              }}
            />
          )}
        </Box>
        <Box
          aria-hidden="true"
          sx={{
            display: 'flex',
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: { xs: '0.625rem', sm: '0.6875rem' },
            letterSpacing: { xs: 0, sm: '0.06em' },
            color: brandTokens.text.secondary,
          }}
        >
          {ZONES.map((zone) => (
            <Box key={zone.status} component="span" sx={{ width: `${zone.width}%`, pr: 0.5, overflow: 'hidden' }}>
              {zone.label}
            </Box>
          ))}
        </Box>
      </Box>

      <Box sx={{ p: 1.5, border: `1px solid ${brandTokens.borders.subtle}`, borderRadius: '10px' }}>
        <Typography sx={{ ...eyebrowSx, fontSize: '0.6875rem', letterSpacing: '0.1em' }}>15-min forecast</Typography>
        <Box data-testid="forecast-value" sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
          {forecastPercent !== null ? (
            <>
              <Typography component="span" sx={{ fontFamily: '"Space Grotesk", sans-serif', fontSize: '1.625rem', fontWeight: 600 }}>
                {`${forecastPercent}%`}
              </Typography>
              {forecastDelta !== null && (
                <Typography component="span" sx={{ fontSize: '0.9375rem', color: brandTokens.text.secondary }}>
                  {`${forecastDelta >= 0 ? '+' : ''}${forecastDelta} pts`}
                </Typography>
              )}
            </>
          ) : (
            <Typography component="span" sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '1.125rem', fontWeight: 600, color: brandTokens.text.muted }}>
              unknown
            </Typography>
          )}
        </Box>
      </Box>

      {recommendation && (
        <Typography sx={{ m: 0, p: 1.5, borderRadius: '10px', bgcolor: alpha(brandTokens.colors.inkBlack, 0.55), fontSize: '0.9375rem' }}>
          <Box
            component="span"
            sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.08em', color: brandTokens.colors.ritualCyan, mr: 1 }}
          >
            NEXT:
          </Box>
          {recommendation}
        </Typography>
      )}
    </Paper>
  );
};

export default LoadInstrument;
