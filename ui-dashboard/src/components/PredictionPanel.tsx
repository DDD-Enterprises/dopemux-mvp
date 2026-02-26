import React from 'react';
import {
  Paper,
  Box,
  Typography,
  LinearProgress,
  Chip,
  Divider,
  Alert,
  Tooltip
} from '@mui/material';
import { TrendingUp, Clock, AlertCircle, Sparkles } from 'lucide-react';
import { brandTokens } from '../theme';

interface PredictionPanelProps {
  prediction?: number;
}

const PredictionPanel: React.FC<PredictionPanelProps> = ({ prediction }) => {
  if (prediction === undefined) {
    return (
      <Paper sx={{ p: 3, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }} className="dopemux-panel">
        <Box sx={{ textAlign: 'center' }}>
          <Clock size={48} style={{ color: brandTokens.colors.aftercareViolet, marginBottom: 16 }} aria-hidden="true" />
          <Typography variant="h6" color="text.secondary">
            Prediction Loading...
          </Typography>
          <LinearProgress sx={{ mt: 2, mb: 2, width: '80%', mx: 'auto', borderRadius: 4 }} aria-label="Loading prediction data" />
          <Typography variant="body2" color="text.secondary">
            LSTM daemon is teasing the future. Hold still.
          </Typography>
        </Box>
      </Paper>
    );
  }

  const getPredictionColor = (pred: number) => {
    if (pred < 0.3) return '#4caf50'; // Low - Green
    if (pred < 0.6) return '#2196f3'; // Optimal - Blue
    if (pred < 0.8) return '#ff9800'; // High - Orange
    return '#f44336'; // Critical - Red
  };

  const getPredictionStatus = (pred: number) => {
    if (pred < 0.3) return 'Low Load Expected';
    if (pred < 0.6) return 'Optimal Zone Expected';
    if (pred < 0.8) return 'High Load Expected';
    return 'Critical Load Expected';
  };

  const getRecommendation = (pred: number) => {
    if (pred < 0.3) return 'Good time for complex tasks or deep focus work';
    if (pred < 0.6) return 'Continue current work patterns - flow state likely';
    if (pred < 0.8) return 'Consider task simplification or strategic breaks';
    return 'Immediate break recommended - cognitive overload imminent';
  };

  const color = getPredictionColor(prediction);

  return (
    <Paper sx={{ p: 3, height: '100%', borderRadius: 4 }} className="dopemux-panel">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1.5 }}>
        <TrendingUp size={24} aria-hidden="true" />
        <Typography variant="h6" sx={{ letterSpacing: '0.12em' }}>15-Minute Prediction</Typography>
        <Tooltip title="Predictive LSTM model running on edge device" arrow>
          <Chip
            size="small"
            label="[EDGE]"
            className="dopemux-chip"
            tabIndex={0}
            sx={{ ml: 'auto', borderColor: 'rgba(255, 139, 209, 0.7)', color: brandTokens.colors.gremlinPink }}
          />
        </Tooltip>
      </Box>
      <Typography className="dopemux-roast" sx={{ mb: 2 }}>
        I edge your curiosity until the model finally spills percentages.
      </Typography>

      {/* Prediction Value */}
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h2"
          sx={{
            color: color,
            fontWeight: 'bold',
            textAlign: 'center',
            mb: 1,
            fontFamily: '"Space Grotesk", sans-serif'
          }}
        >
          {(prediction * 100).toFixed(0)}%
        </Typography>
        <Typography
          variant="subtitle1"
          sx={{ textAlign: 'center', color: color, fontWeight: 'medium' }}
        >
          {getPredictionStatus(prediction)}
        </Typography>
      </Box>

      {/* Visual Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <LinearProgress
          variant="determinate"
          value={prediction * 100}
          aria-label="15-Minute Load Prediction Percentage"
          aria-valuetext={`${(prediction * 100).toFixed(0)}%`}
          sx={{
            height: 16,
            borderRadius: 8,
            bgcolor: 'rgba(255, 255, 255, 0.08)',
            '& .MuiLinearProgress-bar': {
              bgcolor: color,
              borderRadius: 8,
              boxShadow: `0 0 20px ${color}`
            }
          }}
        />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
          <Typography variant="caption" color="text.secondary">Low</Typography>
          <Typography variant="caption" color="text.secondary">Optimal</Typography>
          <Typography variant="caption" color="text.secondary">High</Typography>
          <Typography variant="caption" color="text.secondary">Critical</Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Recommendation */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
          AI Recommendation:
        </Typography>
        <Typography variant="body2">
          {getRecommendation(prediction)}
        </Typography>
      </Box>

      {/* Model Confidence (simulated) */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <AlertCircle size={14} aria-hidden="true" />
          Model Confidence: 82% (based on 30-day training data)
        </Typography>
      </Box>

      {/* ADHD-Friendly Features */}
      <Alert severity="info" sx={{ mt: 2, bgcolor: 'rgba(4,22,40,0.6)', color: brandTokens.colors.serumMint }}>
        <Typography variant="caption">
          <Sparkles size={12} style={{ marginRight: 6 }} aria-hidden="true" />
          <strong>ADHD Optimization:</strong> Predictions update every 5 minutes. Critical load alerts trigger ritual breaks + hydration orders.
        </Typography>
      </Alert>
      <Typography className="dopemux-aftercare" sx={{ mt: 1.5 }}>
        [AFTERCARE] Log the plan, sip water, thank the daemon when you're ready for chaos again.
      </Typography>
    </Paper>
  );
};

export default PredictionPanel;
