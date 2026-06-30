import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Brain } from 'lucide-react';

import { brandTokens, statusStyles } from '../theme';

interface CognitiveLoadGaugeProps {
  load: number;
  status: keyof typeof statusStyles;
  recommendation: string;
}

export default function CognitiveLoadGauge({
  load,
  status,
  recommendation,
}: CognitiveLoadGaugeProps) {
  const statusMeta = statusStyles[status];
  const normalizedLoad = Math.max(0, Math.min(100, Math.round(load * 100)));

  return (
    <Tooltip title={`AI Recommendation: ${recommendation}`} arrow>
      <Paper
        tabIndex={0}
        aria-label={`Cognitive load ${normalizedLoad} percent, ${statusMeta.label}. AI Recommendation: ${recommendation}`}
        sx={{
          p: 3,
          minHeight: 300,
          borderRadius: 3,
          background: brandTokens.gradients.focusCard,
          border: `1px solid ${statusMeta.border}`,
          cursor: 'help',
          outline: 'none',
          transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
          '@keyframes load-pulse': {
            '0%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0.4)}` },
            '70%': { boxShadow: `0 0 0 12px ${alpha(statusMeta.color, 0)}` },
            '100%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0)}` },
          },
          animation: status === 'high' || status === 'critical' ? 'load-pulse 2s infinite' : 'none',
          '@media (prefers-reduced-motion: reduce)': {
            animation: 'none',
          },
          '&:hover, &:focus-visible': {
            transform: 'translateY(-4px)',
            borderColor: statusMeta.color,
            boxShadow: `0 0 20px ${alpha(statusMeta.color, 0.2)}`,
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 0.5 }}>
          <Brain size={18} color={brandTokens.colors.saintGold} aria-hidden="true" />
          <Typography variant="overline" color="text.secondary">
            Cognitive Load
          </Typography>
        </Box>
        <Typography variant="h2" sx={{ color: statusMeta.color, my: 1 }}>
          {normalizedLoad}%
        </Typography>
        <Box aria-hidden="true" sx={{ width: 28, height: 2, bgcolor: statusMeta.color, mb: 1 }} />
        <LinearProgress
          aria-label="Cognitive Load Percentage"
          aria-valuetext={`${normalizedLoad}%`}
          variant="determinate"
          value={normalizedLoad}
          sx={{
            height: 10,
            borderRadius: 6,
            backgroundColor: alpha(statusMeta.color, 0.14),
            '& .MuiLinearProgress-bar': {
              backgroundColor: statusMeta.color,
            },
          }}
        />
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" sx={{ mb: 0.5 }}>{statusMeta.label}</Typography>
          <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 0.5, lineHeight: 1.2 }}>
            AI Recommendation
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {recommendation}
          </Typography>
        </Box>
      </Paper>
    </Tooltip>
  );
}
