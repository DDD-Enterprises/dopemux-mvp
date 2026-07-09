import { useCallback, useState } from 'react';
import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Check, TrendingUp } from 'lucide-react';

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
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    if (!navigator.clipboard?.writeText || !hasPrediction) return;
    try {
      await navigator.clipboard.writeText(`15-min Forecast: ${value}% (${statusMeta.label}) - ${roast}`);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy forecast:', err);
    }
  }, [hasPrediction, value, statusMeta.label, roast]);

  const isPredictiveHigh = status === 'high' || status === 'critical';

  return (
    <Tooltip arrow title={isCopied ? 'Forecast copied!' : hasPrediction ? `15-min forecast: ${statusMeta.label} (${value}%). ${roast}` : 'AI-driven load projection'}>
      <Paper
        role="button"
        tabIndex={hasPrediction ? 0 : -1}
        onClick={handleCopy}
        onKeyDown={(e) => { if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); void handleCopy(); } }}
        aria-label={isCopied ? 'Forecast copied' : hasPrediction ? `15-min prediction ${value}%, ${statusMeta.label}. ${roast}. Click to copy.` : 'No prediction'}
        sx={{
          p: 3, minHeight: 300, borderRadius: 3, background: brandTokens.gradients.focusCard, border: '1px solid transparent', cursor: hasPrediction ? 'copy' : 'default', outline: 'none', transition: 'all 0.2s',
          animation: isPredictiveHigh ? 'predictive-pulse 2s infinite' : 'none',
          '@keyframes predictive-pulse': { '0%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0.4)}` }, '70%': { boxShadow: `0 0 0 12px ${alpha(statusMeta.color, 0)}` }, '100%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0)}` } },
          '&:hover, &:focus-visible': { transform: 'translateY(-4px)', borderColor: statusMeta.color, boxShadow: `0 0 20px ${alpha(statusMeta.color, 0.2)}` },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 0.5 }}>
          {isCopied ? <Check size={18} color={brandTokens.colors.serumMint} /> : <TrendingUp size={18} color={statusMeta.color} />}
          <Typography variant="overline" color="text.secondary">15-minute forecast</Typography>
        </Box>
        <Typography variant="h3" sx={{ color: statusMeta.color, my: 1 }}>{hasPrediction ? `${value}%` : 'N/A'}</Typography>
        <Box aria-hidden="true" sx={{ width: 28, height: 2, bgcolor: statusMeta.color, mb: 1 }} />
        <LinearProgress
          aria-label="15-Minute Load Prediction Percentage"
          variant={hasPrediction ? 'determinate' : 'indeterminate'}
          value={value}
          sx={{ height: 8, borderRadius: 6, backgroundColor: alpha(statusMeta.color, 0.14), '& .MuiLinearProgress-bar': { backgroundColor: statusMeta.color } }}
        />
        <Box sx={{ mt: 3, p: 2, borderRadius: 2, bgcolor: alpha(statusMeta.color, 0.04), border: `1px dashed ${alpha(statusMeta.color, 0.3)}` }}>
          <Typography variant="body2" className="dopemux-roast">{roast}</Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>{hasPrediction ? 'Forecast panel uses backend projection.' : 'Loading...'}</Typography>
        </Box>
      </Paper>
    </Tooltip>
  );
}
