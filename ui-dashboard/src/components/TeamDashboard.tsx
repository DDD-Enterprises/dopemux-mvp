import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  Grid,
  Avatar,
  Chip,
  LinearProgress
} from '@mui/material';
import { Users } from 'lucide-react';
import { brandTokens, statusStyles } from '../theme';

interface TeamMember {
  id: string;
  name: string;
  avatar?: string;
  energy: number;
  attention: number;
  load: number;
  status: 'low' | 'optimal' | 'high' | 'critical';
  role: string;
  currentTask: string;
}

const TeamDashboard: React.FC = () => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    {
      id: '1',
      name: 'Alice Johnson',
      avatar: 'A',
      energy: 0.8,
      attention: 0.7,
      load: 0.4,
      status: 'optimal',
      role: 'Lead Developer',
      currentTask: 'Implementing ML pipeline'
    },
    {
      id: '2',
      name: 'Bob Smith',
      avatar: 'B',
      energy: 0.6,
      attention: 0.5,
      load: 0.7,
      status: 'high',
      role: 'Frontend Engineer',
      currentTask: 'UI dashboard components'
    },
    {
      id: '3',
      name: 'Carol Davis',
      avatar: 'C',
      energy: 0.9,
      attention: 0.8,
      load: 0.3,
      status: 'low',
      role: 'DevOps Engineer',
      currentTask: 'Kubernetes manifests'
    },
    {
      id: '4',
      name: 'David Wilson',
      avatar: 'D',
      energy: 0.4,
      attention: 0.3,
      load: 0.8,
      status: 'critical',
      role: 'Data Engineer',
      currentTask: 'ETL pipeline setup'
    }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setTeamMembers(prev => prev.map(member => ({
        ...member,
        energy: Math.max(0.1, Math.min(1.0, member.energy + (Math.random() - 0.5) * 0.1)),
        attention: Math.max(0.1, Math.min(1.0, member.attention + (Math.random() - 0.5) * 0.1)),
        load: Math.max(0.1, Math.min(1.0, member.load + (Math.random() - 0.5) * 0.05))
      })));
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getTeamLoadAverage = () => {
    const average = teamMembers.reduce((sum, member) => sum + member.load, 0) / teamMembers.length;
    return average;
  };

  const teamLoadAvg = getTeamLoadAverage();

  return (
    <Paper sx={{ p: 3, height: '100%', borderRadius: 4 }} className="dopemux-panel">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 1.5 }}>
        <Users size={24} aria-hidden="true" />
        <Typography variant="h6" sx={{ letterSpacing: '0.15em' }}>
          Team Cognitive Status
        </Typography>
        <Chip
          label={`${(teamLoadAvg * 100).toFixed(0)}% Average Load`}
          sx={{
            ml: 'auto',
            bgcolor: 'rgba(148, 250, 219, 0.08)',
            color: brandTokens.colors.serumMint,
            border: '1px solid rgba(148, 250, 219, 0.4)'
          }}
        />
      </Box>
      <Typography className="dopemux-roast" sx={{ mb: 2 }}>
        Your team is a choir of gremlins; I keep them harmonized with status chips and thinly veiled threats.
      </Typography>

      {/* Team Load Progress */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Team Cognitive Load
        </Typography>
        <LinearProgress
          variant="determinate"
          value={teamLoadAvg * 100}
          aria-label="Team Average Cognitive Load Percentage"
          aria-valuetext={`${(teamLoadAvg * 100).toFixed(0)}%`}
          sx={{
            height: 12,
            borderRadius: 6,
            bgcolor: 'rgba(255, 255, 255, 0.08)',
            '& .MuiLinearProgress-bar': {
              bgcolor: teamLoadAvg < 0.3
                ? statusStyles.low.color
                : teamLoadAvg < 0.6
                ? statusStyles.optimal.color
                : teamLoadAvg < 0.8
                ? statusStyles.high.color
                : statusStyles.critical.color,
              borderRadius: 6,
              boxShadow: '0 0 20px rgba(125, 251, 246, 0.35)'
            }
          }}
        />
      </Box>

      <Grid container spacing={2}>
        {teamMembers.map(member => (
          <Grid item xs={12} sm={6} md={3} key={member.id}>
            <Paper sx={{ p: 2, height: 220, borderRadius: 3 }} className="dopemux-panel">
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'rgba(125, 251, 246, 0.2)', color: brandTokens.colors.serumMint, mr: 2 }}>
                  {member.avatar}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {member.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {member.role}
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={member.status.toUpperCase()}
                  sx={{
                    bgcolor: `${statusStyles[member.status].color}22`,
                    color: statusStyles[member.status].color,
                    border: `1px solid ${statusStyles[member.status].color}`
                  }}
                />
              </Box>

              <Typography variant="body2" sx={{ mb: 1 }}>
                {member.currentTask}
              </Typography>

              <LinearProgress
                variant="determinate"
                value={member.load * 100}
                aria-label={`${member.name}'s Cognitive Load Percentage`}
                aria-valuetext={`${(member.load * 100).toFixed(0)}%`}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: statusStyles[member.status].color,
                    borderRadius: 4
                  }
                }}
              />

              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Chip
                  size="small"
                  label={`${(member.energy * 100).toFixed(0)}% Energy`}
                  sx={{
                    bgcolor: 'rgba(4,22,40,0.7)',
                    color: member.energy > 0.6 ? brandTokens.colors.serumMint : brandTokens.colors.giltEdge,
                    border: `1px solid ${
                      member.energy > 0.6 ? brandTokens.colors.serumMint : brandTokens.colors.giltEdge
                    }`
                  }}
                />
                <Chip
                  size="small"
                  label={`${(member.attention * 100).toFixed(0)}% Attention`}
                  sx={{
                    bgcolor: 'rgba(4,22,40,0.7)',
                    color: member.attention > 0.6 ? brandTokens.colors.ritualCyan : brandTokens.colors.giltEdge,
                    border: `1px solid ${
                      member.attention > 0.6 ? brandTokens.colors.ritualCyan : brandTokens.colors.giltEdge
                    }`
                  }}
                />
              </Box>

              <Typography className="dopemux-roast" sx={{ mt: 1 }}>
                {member.status === 'critical'
                  ? "[BLOCKER] Send this dev water and a hug. Now."
                  : "I archive every sigh they make. Use the intel."}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Team Coordination Notes */}
      <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 1 }}>
        <Typography variant="caption">
          <strong>Team Coordination:</strong> David (Data Engineer) is in critical load - consider
          reassigning tasks or scheduling a team break. Team average load is optimal for collaborative work.
        </Typography>
      </Box>
    </Paper>
  );
};

export default TeamDashboard;
