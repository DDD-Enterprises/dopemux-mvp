import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { TrendingUp } from 'lucide-react';

import { brandTokens, statusStyles, deriveStatus, getDynamicRoast } from '../theme';

interface PredictionPanelProps {
  prediction?: number;
}

export default function PredictionPanel({ prediction }: PredictionPanelProps) {
  const hasPrediction = typeof prediction === 'number';
  const value = hasPrediction ? Math.max(0, Math.min(100, Math.round(prediction * 100))) : 0;
  const status = hasPrediction ? deriveStatus(prediction) : 'optimal';
  const statusMeta = statusStyles[status];
  const roast = getDynamicRoast('15-min Prediction', prediction ?? null);

  const isPredictiveHigh = status === 'high' || status === 'critical';

  return (
    <Tooltip
      title={
        hasPrediction
          ? `15-minute forecast: ${statusMeta.label} (${value}%). ${roast}`
          : '15-minute forecast: AI-driven projection of your cognitive load'
      }
      arrow
    >
      <Paper
        tabIndex={0}
        aria-label={
          hasPrediction
            ? `Fifteen minute prediction ${value} percent, ${statusMeta.label}. ${roast}`
            : 'No prediction available'
        }
        sx={{
          p: 3,
          minHeight: 300,
          borderRadius: 3,
          background: brandTokens.gradients.focusCard,
          border: '1px solid transparent',
          cursor: 'help',
          outline: 'none',
          transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
          '@keyframes predictive-pulse': {
            '0%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0.4)}` },
            '70%': { boxShadow: `0 0 0 12px ${alpha(statusMeta.color, 0)}` },
            '100%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0)}` },
          },
          animation: isPredictiveHigh ? 'predictive-pulse 2s infinite' : 'none',
          '&:hover, &:focus-visible': {
            transform: 'translateY(-4px)',
            borderColor: statusMeta.color,
            boxShadow: `0 0 20px ${alpha(statusMeta.color, 0.2)}`,
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 0.5 }}>
          <TrendingUp size={18} color={statusMeta.color} aria-hidden="true" />
          <Typography variant="overline" color="text.secondary">
            15-minute forecast
          </Typography>
        </Box>
        <Typography variant="h3" sx={{ color: statusMeta.color, my: 1 }}>
          {hasPrediction ? `${value}%` : 'N/A'}
        </Typography>
        <Box aria-hidden="true" sx={{ width: 28, height: 2, bgcolor: statusMeta.color, mb: 1 }} />
        <LinearProgress
          aria-label="15-Minute Load Prediction Percentage"
          aria-valuetext={hasPrediction ? `${value}%` : 'Prediction Loading...'}
          variant={hasPrediction ? 'determinate' : 'indeterminate'}
          value={value}
          sx={{
            height: 8,
            borderRadius: 6,
            backgroundColor: alpha(statusMeta.color, 0.14),
            '& .MuiLinearProgress-bar': {
              backgroundColor: statusMeta.color,
            },
          }}
        />
        <Box sx={{ mt: 3 }}>
          <Typography variant="body2" className="dopemux-roast">
            {roast}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {hasPrediction
              ? 'Forecast panel uses the backend projected cognitive load.'
              : 'Prediction Loading...'}
          </Typography>
        </Box>
      </Paper>
    </Tooltip>
  );
}
