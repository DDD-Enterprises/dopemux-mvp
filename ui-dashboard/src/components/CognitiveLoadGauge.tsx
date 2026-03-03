import React from 'react';
import { Paper, Box, Typography, LinearProgress, Chip, Tooltip } from '@mui/material';
import { Brain, AlertTriangle, CheckCircle, XCircle, Droplet } from 'lucide-react';
import { statusStyles } from '../theme';

interface CognitiveLoadGaugeProps {
  load: number;
  status: 'low' | 'optimal' | 'high' | 'critical';
  recommendation: string;
}

const CognitiveLoadGauge: React.FC<CognitiveLoadGaugeProps> = ({
  load,
  status,
  recommendation
}) => {
  const tone = statusStyles[status];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'low': return <CheckCircle size={20} color={statusStyles.low.color} aria-hidden="true" />;
      case 'optimal': return <CheckCircle size={20} color={statusStyles.optimal.color} aria-hidden="true" />;
      case 'high': return <AlertTriangle size={20} color={statusStyles.high.color} aria-hidden="true" />;
      case 'critical': return <XCircle size={20} color={statusStyles.critical.color} aria-hidden="true" />;
      default: return <Brain size={20} aria-hidden="true" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'low': return 'Low Load - Ready for Complex Tasks';
      case 'optimal': return 'Optimal Zone - Flow State Active';
      case 'high': return 'High Load - Consider Simplification';
      case 'critical': return 'Critical Load - Break Required';
      default: return 'Unknown Status';
    }
  };

  return (
    <Paper sx={{ p: 3, height: '100%', borderRadius: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Brain size={24} style={{ marginRight: 8 }} aria-hidden="true" />
        <Typography variant="h6">Cognitive Load</Typography>
      </Box>

      {/* Status Chip */}
      <Box sx={{ mb: 2 }}>
        <Tooltip title="Current cognitive state based on real-time bio-metrics" arrow>
          <Chip
            icon={getStatusIcon(status)}
            label={getStatusLabel(status)}
            tabIndex={0}
            sx={{
              bgcolor: `${tone.color}22`,
              color: tone.color,
              border: `1px solid ${tone.color}`,
              fontWeight: 'bold',
            }}
          />
        </Tooltip>
      </Box>

      {/* Load Percentage */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ color: tone.color, fontWeight: 'bold' }}>
          {(load * 100).toFixed(0)}%
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Current Cognitive Load
        </Typography>
      </Box>

      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <LinearProgress
          variant="determinate"
          value={load * 100}
          aria-label="Cognitive Load Percentage"
          aria-valuetext={`${(load * 100).toFixed(0)}%`}
          sx={{
            height: 12,
            borderRadius: 6,
            bgcolor: 'rgba(255, 255, 255, 0.06)',
            '& .MuiLinearProgress-bar': {
              bgcolor: tone.color,
              borderRadius: 6,
              boxShadow: `0 0 20px ${tone.color}`,
            }
          }}
        />
      </Box>

      {/* Recommendation */}
      <Box sx={{ p: 2, bgcolor: 'rgba(2, 6, 23, 0.45)', borderRadius: 2, border: `1px dashed rgba(148, 250, 219, 0.4)` }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
          Recommendation:
        </Typography>
        <Typography variant="body2">
          {recommendation}
        </Typography>
      </Box>

      <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 0.6 }}>
        <Typography className="dopemux-roast">
          {status === 'critical'
            ? "[BLOCKER] You're cooked. Drop everything and sip water."
            : "I log your restraint, even when you pretend you don't need any."}
        </Typography>
        <Typography className="dopemux-aftercare">
          <Droplet size={14} style={{ marginRight: 6 }} aria-hidden="true" />
          Logged. Hydrate. Ask nicely if you want aftercare.
        </Typography>
      </Box>
    </Paper>
  );
};

export default CognitiveLoadGauge;
