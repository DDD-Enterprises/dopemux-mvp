import { useCallback, useEffect, useRef, useState } from 'react';
import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Check, TrendingUp } from 'lucide-react';

import { brandTokens, statusStyles, deriveStatus, getDynamicRoast } from '../theme';

interface PredictionPanelProps {
  prediction?: number;
  onError?: (message: string) => void;
}

export default function PredictionPanel({ prediction, onError }: PredictionPanelProps) {
  const hasPrediction = typeof prediction === 'number';
  const value = hasPrediction ? Math.max(0, Math.min(100, Math.round(prediction * 100))) : 0;
  const status = hasPrediction ? deriveStatus(prediction) : 'optimal';
  const statusMeta = statusStyles[status];
  const roast = getDynamicRoast('15-min Prediction', prediction ?? null);
  const [isCopied, setIsCopied] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = useCallback(async () => {
    if (!hasPrediction) return;

    if (!navigator.clipboard?.writeText) {
      onError?.('Clipboard API is not supported in this browser or context.');
      return;
    }

    try {
      await navigator.clipboard.writeText(`15-min Forecast: ${value}% (${statusMeta.label}) - ${roast}`);
      setIsCopied(true);

      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setIsCopied(false);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      onError?.(`Failed to copy forecast: ${errorMsg}`);
    }
  }, [hasPrediction, value, statusMeta.label, roast, onError]);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
        copyTimeoutRef.current = null;
      }
    };
  }, []);

  const isPredictiveHigh = status === 'high' || status === 'critical';
  const copyLabel = isCopied
    ? 'Forecast copied'
    : hasPrediction
      ? `15-min prediction ${value}%, ${statusMeta.label}. ${roast}. Click to copy.`
      : 'No prediction';

  return (
    <Paper
      sx={{
        p: 3,
        minHeight: 300,
        borderRadius: 3,
        background: brandTokens.gradients.focusCard,
        border: '1px solid transparent',
        outline: 'none',
        transition: 'all 0.2s',
        animation: isPredictiveHigh ? 'predictive-pulse 2s infinite' : 'none',
        '@keyframes predictive-pulse': {
          '0%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0.4)}` },
          '70%': { boxShadow: `0 0 0 12px ${alpha(statusMeta.color, 0)}` },
          '100%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0)}` },
        },
        '&:hover': {
          transform: 'translateY(-4px)',
          borderColor: statusMeta.color,
          boxShadow: `0 0 20px ${alpha(statusMeta.color, 0.2)}`,
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 0.5 }}>
        {isCopied ? (
          <Check size={18} color={brandTokens.colors.serumMint} aria-hidden="true" />
        ) : (
          <TrendingUp size={18} color={statusMeta.color} aria-hidden="true" />
        )}
        <Typography variant="overline" color="text.secondary">15-minute forecast</Typography>
      </Box>
      <Typography variant="h3" sx={{ color: statusMeta.color, my: 1 }}>
        {hasPrediction ? `${value}%` : 'N/A'}
      </Typography>
      <Box aria-hidden="true" sx={{ width: 28, height: 2, bgcolor: statusMeta.color, mb: 1 }} />
      <LinearProgress
        aria-label="15-Minute Load Prediction Percentage"
        aria-valuetext={hasPrediction ? `${value}%` : 'Loading prediction'}
        variant={hasPrediction ? 'determinate' : 'indeterminate'}
        value={value}
        sx={{
          height: 8,
          borderRadius: 6,
          backgroundColor: alpha(statusMeta.color, 0.14),
          '& .MuiLinearProgress-bar': { backgroundColor: statusMeta.color },
        }}
      />
      <Tooltip
        arrow
        title={
          isCopied
            ? 'Forecast copied!'
            : hasPrediction
              ? `15-min forecast: ${statusMeta.label} (${value}%). ${roast}`
              : 'AI-driven load projection'
        }
      >
        <Box
          role="button"
          tabIndex={hasPrediction ? 0 : -1}
          aria-disabled={!hasPrediction}
          aria-label={copyLabel}
          onClick={hasPrediction ? () => { void handleCopy(); } : undefined}
          onKeyDown={
            hasPrediction
              ? (e) => {
                  if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) {
                    e.preventDefault();
                    void handleCopy();
                  }
                }
              : undefined
          }
          sx={{
            mt: 3,
            p: 2,
            borderRadius: 2,
            bgcolor: alpha(statusMeta.color, 0.04),
            border: `1px dashed ${alpha(statusMeta.color, 0.3)}`,
            cursor: hasPrediction ? 'copy' : 'default',
            outline: 'none',
            transition: 'all 0.2s ease',
            opacity: hasPrediction ? 1 : 0.72,
            '&:hover, &:focus-visible': hasPrediction
              ? {
                  bgcolor: alpha(statusMeta.color, 0.08),
                  borderColor: statusMeta.color,
                  transform: 'translateY(-2px)',
                  boxShadow: `0 4px 12px ${alpha(statusMeta.color, 0.15)}`,
                }
              : {},
            ...(isCopied && {
              animation: 'forecast-copy-pulse 0.4s ease-out',
              '@keyframes forecast-copy-pulse': {
                '0%': { transform: 'scale(1)' },
                '50%': {
                  transform: 'scale(1.02)',
                  boxShadow: `0 0 12px ${alpha(brandTokens.colors.serumMint, 0.4)}`,
                },
                '100%': { transform: 'scale(1)' },
              },
            }),
          }}
        >
          <Typography variant="body2" className="dopemux-roast">{roast}</Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {hasPrediction ? 'Forecast panel uses backend projection. Click to copy.' : 'Loading...'}
          </Typography>
        </Box>
      </Tooltip>
    </Paper>
  );
}
