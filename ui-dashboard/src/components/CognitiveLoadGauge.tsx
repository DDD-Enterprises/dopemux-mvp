import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';

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
    <Paper
      aria-label={`Cognitive load ${normalizedLoad} percent, ${statusMeta.label}`}
      sx={{
        p: 3,
        minHeight: 300,
        borderRadius: 3,
        background: brandTokens.gradients.focusCard,
        border: `1px solid ${statusMeta.border}`,
      }}
    >
      <Typography variant="overline" color="text.secondary">
        Cognitive Load
      </Typography>
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
        <Typography variant="h6">{statusMeta.label}</Typography>
        <Tooltip title={`Recommendation: ${recommendation}`} arrow>
          <Typography variant="body2" color="text.secondary" tabIndex={0}>
            {recommendation}
          </Typography>
        </Tooltip>
      </Box>
    </Paper>
  );
}
