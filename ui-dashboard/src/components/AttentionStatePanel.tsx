import React from 'react';
import { Box, Paper, Tooltip, Typography } from '@mui/material';

import { AttentionState, ENERGY_LEVELS, EnergyLevel } from '../cognitiveReading';
import { brandTokens } from '../theme';

interface AttentionStatePanelProps {
  /** Raw ADHD engine enum, e.g. `medium`. `null` when no reading. */
  energyLevel: EnergyLevel | null;
  /** Raw ADHD engine enum, e.g. `focused`. `null` when no reading. */
  attentionState: AttentionState | null;
}

const ATTENTION_COLORS: Record<AttentionState, string> = {
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
          <Tooltip title={energyLevel ? `Energy level: ${humanize(energyLevel)} (${energyStep + 1}/${ENERGY_LEVELS.length})` : 'Energy level: unknown'} arrow>
            <Box
              tabIndex={0}
              aria-label={energyLevel ? `Energy level: ${humanize(energyLevel)}, step ${energyStep + 1} of ${ENERGY_LEVELS.length}` : 'Energy level: unknown'}
              sx={{ display: 'inline-flex', alignItems: 'center', gap: 1.5, cursor: 'help', outline: 'none', borderRadius: 1, '&:focus-visible': { boxShadow: `0 0 0 2px ${brandTokens.colors.serumMint}` } }}
            >
              {energyStep >= 0 && (
                <Box aria-hidden="true" sx={{ display: 'flex', gap: '3px' }}>
                  {ENERGY_LEVELS.map((level, index) => (
                    <Box key={level} sx={{ width: 14, height: 8, borderRadius: '2px', bgcolor: index <= energyStep ? brandTokens.colors.serumMint : brandTokens.borders.subtle }} />
                  ))}
                </Box>
              )}
              <Typography component="span" sx={energyLevel ? valueSx : unknownSx}>
                {energyLevel ? humanize(energyLevel) : 'unknown'}
              </Typography>
            </Box>
          </Tooltip>
        </dd>
        <dt>Attention</dt>
        <dd data-testid="attention-value">
          <Tooltip title={attentionState ? `Attention state: ${humanize(attentionState)}` : 'Attention state: unknown'} arrow>
            <Box
              tabIndex={0}
              aria-label={attentionState ? `Attention state: ${humanize(attentionState)}` : 'Attention state: unknown'}
              sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'help', outline: 'none', borderRadius: 1, '&:focus-visible': { boxShadow: `0 0 0 2px ${attentionState ? ATTENTION_COLORS[attentionState] : brandTokens.colors.ritualCyan}` } }}
            >
              <Typography component="span" sx={attentionState ? { ...valueSx, color: ATTENTION_COLORS[attentionState] } : unknownSx}>
                {attentionState ? humanize(attentionState) : 'unknown'}
              </Typography>
            </Box>
          </Tooltip>
        </dd>
      </Box>
    </Paper>
  );
};

export default AttentionStatePanel;
