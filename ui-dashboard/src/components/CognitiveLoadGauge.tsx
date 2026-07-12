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
  const statusMeta = statusStyles[status];
  const normalizedLoad = Math.max(0, Math.min(100, Math.round(load * 100)));
  const roast = getDynamicRoast('Cognitive Load', load);

  const [isCopied, setIsCopied] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = useCallback(async () => {
    if (!navigator.clipboard?.writeText) {
      onError?.('Clipboard API is not supported in this browser or context.');
      return;
    }
    try {
      await navigator.clipboard.writeText(`Cognitive Load: ${normalizedLoad}% (${statusMeta.label}) - AI Recommendation: ${recommendation}`);
      setIsCopied(true);
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setIsCopied(false);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      onError?.(`Failed to copy recommendation: ${errorMsg}`);
    }
  }, [normalizedLoad, statusMeta.label, recommendation, onError]);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
        copyTimeoutRef.current = null;
      }
    };
  }, []);

  return (
    <Tooltip title={isCopied ? 'Copied!' : `AI Recommendation: ${recommendation}. Click to copy details.`} arrow>
      <Paper
        role="button"
        tabIndex={0}
        onClick={handleCopy}
        onKeyDown={(e) => {
          if (e.repeat) return;
          if (e.key === ' ') e.preventDefault();
          if (e.key === 'Enter') {
            e.preventDefault();
            void handleCopy();
          }
        }}
        onKeyUp={(e) => {
          if (e.repeat) return;
          if (e.key === ' ') {
            e.preventDefault();
            void handleCopy();
          }
        }}
        aria-label={isCopied ? `Recommendation copied: ${recommendation}` : `Cognitive load ${normalizedLoad} percent, ${statusMeta.label}. AI Recommendation: ${recommendation}. Click to copy details.`}
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
          '@keyframes copy-success-glow': {
            '0%': { transform: 'scale(1)' },
            '50%': { transform: 'scale(1.02)', boxShadow: `0 0 20px ${alpha(brandTokens.colors.serumMint, 0.4)}` },
            '100%': { transform: 'scale(1)' },
          },
          animation: isCopied
            ? 'copy-success-glow 0.4s ease-out'
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
          <Typography variant="body2" className="dopemux-roast" sx={{ mb: 1 }}>
            {roast}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Typography variant="overline" color="text.secondary" sx={{ lineHeight: 1.2 }}>
              AI Recommendation
            </Typography>
            {isCopied ? (
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
