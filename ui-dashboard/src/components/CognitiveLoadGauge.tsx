import { useCallback, useEffect, useRef, useState } from 'react';
import { Box, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Brain, Check, Copy } from 'lucide-react';
import { brandTokens, statusStyles, getDynamicRoast } from '../theme';

interface CognitiveLoadGaugeProps {
  load: number;
  status: keyof typeof statusStyles;
  recommendation: string;
  onError?: (message: string) => void;
}

export default function CognitiveLoadGauge({
  load,
  status,
  recommendation,
  onError,
}: CognitiveLoadGaugeProps) {
  const [copied, setCopied] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const statusMeta = statusStyles[status];
  const val = Math.max(0, Math.min(100, Math.round(load * 100)));
  const roast = getDynamicRoast('Cognitive Load', load);

  // Clear copied state if underlying data changes
  useEffect(() => {
    setCopied(false);
    if (copyTimeoutRef.current) {
      clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = null;
    }
  }, [val, status, recommendation]);

  const onCopy = useCallback(async () => {
    if (!navigator.clipboard?.writeText) {
      onError?.('Clipboard API not supported');
      return;
    }
    try {
      await navigator.clipboard.writeText(`Load: ${val}% (${statusMeta.label}) - AI: ${recommendation}`);
      setCopied(true);
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setCopied(false);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch (e) {
      onError?.('Failed to copy load details and recommendation');
    }
  }, [val, statusMeta.label, recommendation, onError]);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    };
  }, []);

  return (
    <Tooltip title={copied ? 'Copied!' : `AI Recommendation: ${recommendation}. Click to copy details.`} arrow>
      <Paper
        role="button"
        tabIndex={0}
        onClick={onCopy}
        onKeyDown={(e) => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            onCopy();
          }
        }}
        aria-label={copied ? 'Copied' : `Load ${val}%, ${statusMeta.label}. AI Recommendation: ${recommendation}. Click to copy details.`}
        sx={{
          p: 3,
          minHeight: 300,
          borderRadius: 3,
          background: brandTokens.gradients.focusCard,
          border: `1px solid ${statusMeta.border}`,
          cursor: 'copy',
          outline: 'none',
          transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
          '@keyframes load-pulse': {
            '0%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0.4)}` },
            '70%': { boxShadow: `0 0 0 12px ${alpha(statusMeta.color, 0)}` },
            '100%': { boxShadow: `0 0 0 0px ${alpha(statusMeta.color, 0)}` },
          },
          '@keyframes copy-glow': {
            '0%': { transform: 'scale(1)' },
            '50%': {
              transform: 'scale(1.02)',
              boxShadow: `0 0 20px ${alpha(brandTokens.colors.serumMint, 0.4)}`,
            },
            '100%': { transform: 'scale(1)' },
          },
          animation: copied
            ? 'copy-glow 0.4s ease-out'
            : (status === 'high' || status === 'critical' ? 'load-pulse 2s infinite' : 'none'),
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
          {val}%
        </Typography>
        <Box aria-hidden="true" sx={{ width: 28, height: 2, bgcolor: statusMeta.color, mb: 1 }} />
        <LinearProgress
          aria-label="Cognitive Load Percentage"
          aria-valuetext={`${val}%`}
          variant="determinate"
          value={val}
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
          <Typography variant="body2" className="dopemux-roast" sx={{ mb: 1 }}>
            {roast}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Typography variant="overline" color="text.secondary" sx={{ lineHeight: 1.2 }}>
              AI Recommendation
            </Typography>
            {copied ? (
              <Check size={14} color={brandTokens.colors.serumMint} aria-hidden="true" />
            ) : (
              <Copy size={14} color={brandTokens.colors.ritualCyan} aria-hidden="true" />
            )}
          </Box>
          <Typography variant="body2" color="text.secondary">
            {recommendation}
          </Typography>
        </Box>
      </Paper>
    </Tooltip>
  );
}
