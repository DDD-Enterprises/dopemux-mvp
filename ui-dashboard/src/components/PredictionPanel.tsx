import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';

import { brandTokens } from '../theme';

interface PredictionPanelProps {
  prediction?: number;
}

export default function PredictionPanel({ prediction }: PredictionPanelProps) {
  const hasPrediction = typeof prediction === 'number';
  const value = hasPrediction ? Math.max(0, Math.min(100, Math.round(prediction * 100))) : 0;

  return (
    <Paper
      aria-label={hasPrediction ? `Fifteen minute prediction ${value} percent` : 'No prediction available'}
      sx={{
        p: 3,
        minHeight: 300,
        borderRadius: 3,
        background: brandTokens.gradients.focusCard,
      }}
    >
      <Typography variant="overline" color="text.secondary">
        15-minute forecast
      </Typography>
      <Typography variant="h3" sx={{ color: brandTokens.colors.giltEdge, my: 1 }}>
        {hasPrediction ? `${value}%` : 'N/A'}
      </Typography>
      <Box aria-hidden="true" sx={{ width: 28, height: 2, bgcolor: brandTokens.colors.giltEdge, mb: 1 }} />
      <Tooltip title="Predictive LSTM model running on edge device" arrow>
        <LinearProgress
          aria-label="15-Minute Load Prediction Percentage"
          aria-valuetext={hasPrediction ? `${value}%` : 'Prediction Loading...'}
          variant={hasPrediction ? 'determinate' : 'indeterminate'}
          value={value}
          sx={{
            height: 8,
            borderRadius: 6,
            backgroundColor: alpha(brandTokens.colors.giltEdge, 0.14),
            '& .MuiLinearProgress-bar': {
              backgroundColor: brandTokens.colors.giltEdge,
            },
          }}
        />
      </Tooltip>
      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          {hasPrediction
            ? 'Forecast panel uses the backend projected cognitive load when available.'
            : 'Prediction Loading...'}
        </Typography>
      </Box>
    </Paper>
  );
}
