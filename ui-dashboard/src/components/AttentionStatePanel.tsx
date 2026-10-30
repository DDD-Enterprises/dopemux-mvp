import React from 'react';
import { Box, Paper, Typography } from '@mui/material';

import { brandTokens } from '../theme';

interface AttentionStatePanelProps {
  /** Raw ADHD engine enum, e.g. `medium`. `null` when no reading. */
  energyLevel: string | null;
  /** Raw ADHD engine enum, e.g. `focused`. `null` when no reading. */
  attentionState: string | null;
}

// Ordered as the ADHD engine reports them; the meter lights one step per level.
const ENERGY_LEVELS = ['very_low', 'low', 'medium', 'high', 'hyperfocus'];

const ATTENTION_COLORS: Record<string, string> = {
  focused: brandTokens.colors.ritualCyan,
  hyperfocused: brandTokens.colors.ritualCyan,
  transitioning: brandTokens.text.primary,
  scattered: brandTokens.colors.giltEdge,
  overwhelmed: brandTokens.colors.giltEdge,
};

const humanize = (value: string) => value.replace(/_/g, ' ');

const valueSx = {
  fontFamily: brandTokens.fonts.display,
  fontSize: '1.25rem',
  fontWeight: 600,
} as const;

const unknownSx = {
  fontFamily: brandTokens.fonts.mono,
  fontSize: '1rem',
  fontWeight: 600,
  color: brandTokens.text.muted,
} as const;

const AttentionStatePanel: React.FC<AttentionStatePanelProps> = ({ energyLevel, attentionState }) => {
  const energyStep = energyLevel ? ENERGY_LEVELS.indexOf(energyLevel) : -1;

  return (
    <Paper
      component="section"
      aria-labelledby="attention-state-title"
      sx={{ p: 3, borderRadius: '18px', display: 'flex', flexDirection: 'column', gap: 1.75 }}
    >
      <Typography
        id="attention-state-title"
        component="h2"
        sx={{
          fontFamily: brandTokens.fonts.mono,
          fontSize: '0.75rem',
          fontWeight: 600,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: brandTokens.text.secondary,
        }}
      >
        Attention State
      </Typography>
      <Box
        component="dl"
        sx={{
          m: 0,
          display: 'grid',
          gridTemplateColumns: 'auto 1fr',
          rowGap: 1.5,
          columnGap: 2,
          alignItems: 'center',
          '& dt': { color: brandTokens.text.secondary },
          '& dd': { m: 0, justifySelf: 'end', display: 'flex', alignItems: 'center', gap: 1.5 },
        }}
      >
        <dt>Energy</dt>
        <dd data-testid="energy-value">
          {energyStep >= 0 && (
            <Box aria-hidden="true" sx={{ display: 'flex', gap: '3px' }}>
              {ENERGY_LEVELS.map((level, index) => (
                <Box
                  key={level}
                  sx={{
                    width: 14,
                    height: 8,
                    borderRadius: '2px',
                    bgcolor: index <= energyStep ? brandTokens.colors.serumMint : brandTokens.borders.subtle,
                  }}
                />
              ))}
            </Box>
          )}
          {energyLevel ? (
            <Typography component="span" sx={valueSx}>
              {humanize(energyLevel)}
            </Typography>
          ) : (
            <Typography component="span" sx={unknownSx}>
              unknown
            </Typography>
          )}
        </dd>
        <dt>Attention</dt>
        <dd data-testid="attention-value">
          {attentionState ? (
            <Typography
              component="span"
              sx={{ ...valueSx, color: ATTENTION_COLORS[attentionState] ?? brandTokens.text.primary }}
            >
              {humanize(attentionState)}
            </Typography>
          ) : (
            <Typography component="span" sx={unknownSx}>
              unknown
            </Typography>
          )}
        </dd>
      </Box>
    </Paper>
  );
};

export default AttentionStatePanel;
