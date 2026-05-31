import { Avatar, Box, Chip, LinearProgress, Paper, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';

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
  const teamAverageLoad = Math.round(
    teamMembers.reduce((total, member) => total + member.load, 0) / teamMembers.length
  );

  return (
    <Paper
      aria-label="Team dashboard signal summary"
      sx={{
        p: 3,
        borderRadius: 3,
        background: brandTokens.gradients.focusCard,
      }}
    >
      <Typography variant="h6" sx={{ mb: 2 }}>
        Team Signal Board
      </Typography>
      <Tooltip title="Average cognitive load across all team members" arrow>
        <LinearProgress
          aria-label="Team Average Cognitive Load Percentage"
          aria-valuetext={`${teamAverageLoad}%`}
          variant="determinate"
          value={teamAverageLoad}
          sx={{ mb: 2, height: 8, borderRadius: 6 }}
        />
      </Tooltip>
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
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar aria-label={`Profile picture of ${member.name}`} sx={{ width: 28, height: 28 }}>
                {member.name[0]}
              </Avatar>
              <Typography variant="body2">{member.name}</Typography>
              <Tooltip title={statusStyles[member.status].label} arrow>
                <Chip size="small" label={statusStyles[member.status].label} />
              </Tooltip>
              <Box aria-hidden="true" sx={{ ml: 'auto', width: 6, height: 6, borderRadius: '50%', bgcolor: statusStyles[member.status].color }} />
            </Box>
            <LinearProgress
              aria-label={`${member.name}'s Cognitive Load Percentage`}
              aria-valuetext={`${member.load}%`}
              variant="determinate"
              value={member.load}
            />
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Tooltip title="Current energy level" arrow>
                <Chip size="small" tabIndex={0} label={`Energy ${member.energy}%`} />
              </Tooltip>
              <Tooltip title="Current attention focus" arrow>
                <Chip size="small" tabIndex={0} label={`Attention ${member.attention}%`} />
              </Tooltip>
            </Box>
          </Box>
        ))}
      </Box>
      <Tooltip title="AI-generated team coordination insights" arrow>
        <Typography variant="body2" color="text.secondary" tabIndex={0} sx={{ mb: 2 }}>
          Sequence handoffs while average load is below escalation threshold.
        </Typography>
      </Tooltip>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
        {teamSignals.map((signal) => (
          <Chip
            key={signal.label}
            label={`${signal.label}: ${signal.value}`}
            sx={{
              color: signal.color,
              border: `1px solid ${alpha(signal.color, 0.55)}`,
              backgroundColor: alpha(signal.color, 0.08),
            }}
            variant="outlined"
          />
        ))}
      </Box>
    </Paper>
  );
}
