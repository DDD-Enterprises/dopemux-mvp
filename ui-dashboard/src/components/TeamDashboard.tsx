import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Avatar, Box, Chip, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Check, Copy, Eye, Zap } from 'lucide-react';

import { brandTokens, statusStyles } from '../theme';

const teamMembers = [
  { name: 'Operator', load: 42, energy: 78, attention: 82, status: 'optimal' },
  { name: 'Implementer', load: 55, energy: 68, attention: 74, status: 'high' },
  { name: 'Reviewer', load: 34, energy: 72, attention: 80, status: 'low' },
] as const;

const teamSignals = [
  { label: 'Queue', value: 'Stable', color: brandTokens.colors.serumMint },
  { label: 'Handoff', value: 'Clear', color: brandTokens.colors.saintGold },
];

export default function TeamDashboard() {
  const [isInsightCopied, setIsInsightCopied] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const teamAverageLoad = Math.round(
    teamMembers.reduce((total, member) => total + member.load, 0) / teamMembers.length
  );

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
      }
    };
  }, []);

  const handleCopyInsight = useCallback(async (text: string) => {
    if (!navigator.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(text);
      setIsInsightCopied(true);

      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setIsInsightCopied(false);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy insight:', err);
    }
  }, []);

  const getStatusFromLoad = (load: number): keyof typeof statusStyles => {
    if (load > 80) return 'critical';
    if (load > 60) return 'high';
    if (load < 30) return 'low';
    return 'optimal';
  };

  const teamStatus = getStatusFromLoad(teamAverageLoad);
  const teamStatusColor = statusStyles[teamStatus].color;

  const teamInsight = 'Sequence handoffs while average load is below escalation threshold.';

  return (
    <Tooltip
      title={`Average Team Load: ${teamAverageLoad}% • ${statusStyles[teamStatus].label}`}
      arrow
    >
      <Paper
        tabIndex={0}
        aria-label={`Team dashboard signal summary. Average load: ${teamAverageLoad}%. Status: ${statusStyles[teamStatus].label}.`}
        sx={{
          p: 3,
          borderRadius: 3,
          background: brandTokens.gradients.focusCard,
          border: '1px solid transparent',
          cursor: 'help',
          outline: 'none',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '@keyframes insight-copy-pulse': {
            '0%': { transform: 'scale(1)' },
            '50%': {
              transform: 'scale(1.02)',
              boxShadow: `0 0 15px ${alpha(brandTokens.colors.serumMint, 0.3)}`,
            },
            '100%': { transform: 'scale(1)' },
          },
          '&:hover, &:focus-visible': {
            transform: 'translateY(-4px)',
            borderColor: teamStatusColor,
            boxShadow: `0 0 20px ${alpha(teamStatusColor, 0.2)}`,
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <Zap size={20} color={brandTokens.colors.ritualCyan} aria-hidden="true" />
          <Typography variant="h6" sx={{ letterSpacing: '0.16em' }}>
            Team Signal Board
          </Typography>
          <Box
            sx={{
              ml: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <Typography variant="caption" sx={{ fontWeight: 'bold', color: teamStatusColor }}>
              {teamAverageLoad}% AVG LOAD
            </Typography>
            <Chip
              size="small"
              label={statusStyles[teamStatus].label}
              sx={{
                bgcolor: alpha(teamStatusColor, 0.1),
                color: teamStatusColor,
                border: `1px solid ${teamStatusColor}`,
                fontWeight: 'bold',
                fontSize: '0.65rem',
              }}
            />
          </Box>
        </Box>
        <LinearProgress
          aria-label="Team Average Cognitive Load Percentage"
          aria-valuetext={`${teamAverageLoad}%`}
          variant="determinate"
          value={teamAverageLoad}
          sx={{
            mb: 2,
            height: 8,
            borderRadius: 6,
            bgcolor: alpha(teamStatusColor, 0.1),
            '& .MuiLinearProgress-bar': {
              bgcolor: teamStatusColor,
              borderRadius: 3,
            },
          }}
        />
      <Box sx={{ display: 'grid', gap: 1.5, mb: 2 }}>
        {teamMembers.map((member) => (
          <Box
            key={member.name}
            tabIndex={0}
            sx={{
              display: 'grid',
              gap: 1,
              p: 1.5,
              borderRadius: 2,
              border: `1px solid ${alpha(statusStyles[member.status].color, 0.4)}`,
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              cursor: 'help',
              '&:hover, &:focus-within': {
                transform: 'translateY(-2px)',
                bgcolor: alpha(statusStyles[member.status].color, 0.05),
                borderColor: statusStyles[member.status].color,
                boxShadow: `0 4px 12px ${alpha(statusStyles[member.status].color, 0.15)}`,
              },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar aria-label={`Profile picture of ${member.name}`} sx={{ width: 28, height: 28 }}>
                {member.name[0]}
              </Avatar>
              <Typography variant="body2">{member.name}</Typography>
              <Tooltip title={statusStyles[member.status].label} arrow>
                <Chip
                  size="small"
                  label={statusStyles[member.status].label}
                  aria-label={`${member.name}'s current status: ${statusStyles[member.status].label}`}
                  tabIndex={0}
                  sx={{ cursor: 'help' }}
                />
              </Tooltip>
              <Box aria-hidden="true" sx={{ ml: 'auto', width: 6, height: 6, borderRadius: '50%', bgcolor: statusStyles[member.status].color }} />
            </Box>
            <LinearProgress
              aria-label={`${member.name}'s Cognitive Load Percentage`}
              aria-valuetext={`${member.load}%`}
              variant="determinate"
              value={member.load}
              sx={{
                height: 6,
                borderRadius: 3,
                bgcolor: alpha(statusStyles[member.status].color, 0.1),
                '& .MuiLinearProgress-bar': {
                  bgcolor: statusStyles[member.status].color,
                  borderRadius: 3,
                },
              }}
            />
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Tooltip title="Current energy level" arrow>
                <Chip
                  size="small"
                  tabIndex={0}
                  icon={<Zap size={14} color={brandTokens.colors.serumMint} aria-hidden="true" />}
                  label={`Energy ${member.energy}%`}
                  aria-label={`${member.name}'s current energy level: ${member.energy}%`}
                  sx={{
                    cursor: 'help',
                    transition: 'all 0.2s ease',
                    border: '1px solid transparent',
                    '&:hover, &:focus-visible': {
                      bgcolor: alpha(brandTokens.colors.serumMint, 0.12),
                      borderColor: brandTokens.colors.serumMint,
                      boxShadow: `0 0 12px ${alpha(brandTokens.colors.serumMint, 0.3)}`,
                      transform: 'translateY(-1px)',
                    },
                  }}
                />
              </Tooltip>
              <Tooltip title="Current attention focus" arrow>
                <Chip
                  size="small"
                  tabIndex={0}
                  icon={<Eye size={14} color={brandTokens.colors.ritualCyan} aria-hidden="true" />}
                  label={`Attention ${member.attention}%`}
                  aria-label={`${member.name}'s current attention focus: ${member.attention}%`}
                  sx={{
                    cursor: 'help',
                    transition: 'all 0.2s ease',
                    border: '1px solid transparent',
                    '&:hover, &:focus-visible': {
                      bgcolor: alpha(brandTokens.colors.ritualCyan, 0.12),
                      borderColor: brandTokens.colors.ritualCyan,
                      boxShadow: `0 0 12px ${alpha(brandTokens.colors.ritualCyan, 0.3)}`,
                      transform: 'translateY(-1px)',
                    },
                  }}
                />
              </Tooltip>
            </Box>
          </Box>
        ))}
      </Box>
      <Box
        role="button"
        tabIndex={0}
        onClick={() => handleCopyInsight(teamInsight)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            void handleCopyInsight(teamInsight);
          }
        }}
        aria-label={
          isInsightCopied
            ? `AI Insight: ${teamInsight} (Copied to clipboard)`
            : `AI Insight: ${teamInsight}. Click to copy to clipboard.`
        }
        sx={{
          mb: 2,
          p: 1.5,
          borderRadius: 2,
          bgcolor: alpha(brandTokens.colors.inkBlack, 0.4),
          border: `1px solid ${alpha(brandTokens.colors.serumMint, 0.2)}`,
          cursor: 'copy',
          transition: 'all 0.2s ease',
          ...(isInsightCopied && {
            animation: 'insight-copy-pulse 0.4s ease-out',
            borderColor: brandTokens.colors.serumMint,
            bgcolor: alpha(brandTokens.colors.serumMint, 0.05),
          }),
          '&:hover, &:focus-visible': {
            borderColor: brandTokens.colors.serumMint,
            bgcolor: alpha(brandTokens.colors.serumMint, 0.08),
            outline: 'none',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          {isInsightCopied ? (
            <Check size={14} color={brandTokens.colors.serumMint} aria-hidden="true" />
          ) : (
            <Copy size={14} color={brandTokens.colors.serumMint} aria-hidden="true" />
          )}
          <Typography
            variant="caption"
            sx={{
              fontWeight: 'bold',
              letterSpacing: '0.1em',
              color: isInsightCopied ? brandTokens.colors.serumMint : brandTokens.text.secondary,
            }}
          >
            {isInsightCopied ? 'COPIED!' : 'AI INSIGHT'}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {teamInsight}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
        {teamSignals.map((signal) => (
          <Tooltip key={signal.label} title={`Team signal: ${signal.label} status`} arrow>
            <Chip
              label={`${signal.label}: ${signal.value}`}
              aria-label={`Team signal: ${signal.label} is ${signal.value}`}
              tabIndex={0}
              sx={{
                color: signal.color,
                border: '1px solid transparent',
                borderColor: alpha(signal.color, 0.55),
                backgroundColor: alpha(signal.color, 0.08),
                cursor: 'help',
                transition: 'all 0.2s ease',
                '&:hover, &:focus-visible': {
                  bgcolor: alpha(signal.color, 0.12),
                  borderColor: signal.color,
                  boxShadow: `0 0 12px ${alpha(signal.color, 0.3)}`,
                  transform: 'translateY(-1px)',
                },
              }}
              variant="outlined"
            />
          </Tooltip>
        ))}
      </Box>
      </Paper>
    </Tooltip>
  );
}
