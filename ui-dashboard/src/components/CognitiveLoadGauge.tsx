import React from 'react';
import { Paper, Box, Typography, LinearProgress, Chip } from '@mui/material';
import { Brain, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

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
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'low': return '#4caf50'; // Green
      case 'optimal': return '#2196f3'; // Blue
      case 'high': return '#ff9800'; // Orange
      case 'critical': return '#f44336'; // Red
      default: return '#9e9e9e';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'low': return <CheckCircle size={20} color="#4caf50" />;
      case 'optimal': return <CheckCircle size={20} color="#2196f3" />;
      case 'high': return <AlertTriangle size={20} color="#ff9800" />;
      case 'critical': return <XCircle size={20} color="#f44336" />;
      default: return <Brain size={20} />;
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
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Brain size={24} style={{ marginRight: 8 }} />
        <Typography variant="h6">Cognitive Load</Typography>
      </Box>

      {/* Status Chip */}
      <Box sx={{ mb: 2 }}>
        <Chip
          icon={getStatusIcon(status)}
          label={getStatusLabel(status)}
          sx={{
            bgcolor: getStatusColor(status),
            color: 'white',
            fontWeight: 'bold'
          }}
        />
      </Box>

      {/* Load Percentage */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ color: getStatusColor(status), fontWeight: 'bold' }}>
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
          sx={{
            height: 12,
            borderRadius: 6,
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              bgcolor: getStatusColor(status),
              borderRadius: 6
            }
          }}
        />
      </Box>

      {/* Recommendation */}
      <Box sx={{ p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 1 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
          Recommendation:
        </Typography>
        <Typography variant="body2">
          {recommendation}
        </Typography>
      </Box>

      {/* ADHD-Friendly Design Notes */}
      <Box sx={{ mt: 2, p: 1, bgcolor: 'rgba(255, 255, 255, 0.03)', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Interface adapts automatically based on cognitive load status
        </Typography>
      </Box>
    </Paper>
  );
};

export default CognitiveLoadGauge;