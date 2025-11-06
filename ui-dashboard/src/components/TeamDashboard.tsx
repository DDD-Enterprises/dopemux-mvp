import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  Grid,
  Avatar,
  Chip,
  LinearProgress,
  Tooltip
} from '@mui/material';
import { Users, Brain, Zap, Eye, TrendingUp } from 'lucide-react';

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'low': return '#4caf50';
      case 'optimal': return '#2196f3';
      case 'high': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getTeamLoadAverage = () => {
    const average = teamMembers.reduce((sum, member) => sum + member.load, 0) / teamMembers.length;
    return average;
  };

  const teamLoadAvg = getTeamLoadAverage();

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Users size={24} style={{ marginRight: 8 }} />
        <Typography variant="h6">Team Cognitive Status</Typography>
        <Chip
          label={`${(teamLoadAvg * 100).toFixed(0)}% Average Load`}
          sx={{
            ml: 2,
            bgcolor: getStatusColor(
              teamLoadAvg < 0.3 ? 'low' :
              teamLoadAvg < 0.6 ? 'optimal' :
              teamLoadAvg < 0.8 ? 'high' : 'critical'
            ),
            color: 'white'
          }}
        />
      </Box>

      {/* Team Load Progress */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Team Cognitive Load
        </Typography>
        <LinearProgress
          variant="determinate"
          value={teamLoadAvg * 100}
          sx={{
            height: 12,
            borderRadius: 6,
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              bgcolor: getStatusColor(
                teamLoadAvg < 0.3 ? 'low' :
                teamLoadAvg < 0.6 ? 'optimal' :
                teamLoadAvg < 0.8 ? 'high' : 'critical'
              ),
              borderRadius: 6
            }
          }}
        />
      </Box>

      <Grid container spacing={2}>
        {teamMembers.map(member => (
          <Grid item xs={12} sm={6} md={3} key={member.id}>
            <Paper sx={{ p: 2, height: 200 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
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
                    bgcolor: getStatusColor(member.status),
                    color: 'white'
                  }}
                />
              </Box>

              <Typography variant="body2" sx={{ mb: 1 }}>
                {member.currentTask}
              </Typography>

              <LinearProgress
                variant="determinate"
                value={member.load * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(member.status),
                    borderRadius: 4
                  }
                }}
              />

              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Chip
                  size="small"
                  label={`${(member.energy * 100).toFixed(0)}% Energy`}
                  sx={{ bgcolor: member.energy > 0.6 ? '#4caf50' : '#ff9800', color: 'white' }}
                />
                <Chip
                  size="small"
                  label={`${(member.attention * 100).toFixed(0)}% Attention`}
                  sx={{ bgcolor: member.attention > 0.6 ? '#2196f3' : '#ff9800', color: 'white' }}
                />
              </Box>
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