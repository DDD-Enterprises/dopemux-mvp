import React, { useState, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  ThemeProvider,
  createTheme,
  CssBaseline,
  useMediaQuery
} from '@mui/material';
import { Brain, Zap, Eye, TrendingUp } from 'lucide-react';

// Import components
import CognitiveLoadGauge from './components/CognitiveLoadGauge';
import TaskSequencer from './components/TaskSequencer';
import TeamDashboard from './components/TeamDashboard';
import PredictionPanel from './components/PredictionPanel';

// Types
interface CognitiveState {
  energy: number;
  attention: number;
  load: number;
  prediction?: number;
  status: 'low' | 'optimal' | 'high' | 'critical';
  recommendation: string;
}

// ADHD-friendly dark theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00bcd4',
    },
    secondary: {
      main: '#ff9800',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontSize: 14,
    h1: { fontSize: '2rem' },
    h2: { fontSize: '1.5rem' },
    h3: { fontSize: '1.25rem' },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

function App() {
  const [cognitiveState, setCognitiveState] = useState<CognitiveState>({
    energy: 0.7,
    attention: 0.6,
    load: 0.5,
    status: 'optimal',
    recommendation: 'Continue current work patterns'
  });

  const [socket, setSocket] = useState<Socket | null>(null);
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Connect to real-time data
  useEffect(() => {
    const newSocket = io('http://localhost:3001', {
      transports: ['websocket', 'polling']
    });

    newSocket.on('cognitive-update', (data: CognitiveState) => {
      setCognitiveState(data);
    });

    newSocket.on('prediction-update', (prediction: number) => {
      setCognitiveState(prev => ({
        ...prev,
        prediction
      }));
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  // Adaptive layout based on cognitive load
  const getLayoutConfig = () => {
    if (cognitiveState.status === 'critical') {
      // Simplified layout for high cognitive load
      return {
        showTeamDashboard: false,
        showPredictions: false,
        compactMode: true
      };
    } else if (cognitiveState.status === 'high') {
      // Reduced complexity
      return {
        showTeamDashboard: false,
        showPredictions: true,
        compactMode: false
      };
    } else {
      // Full layout for optimal/low load
      return {
        showTeamDashboard: true,
        showPredictions: true,
        compactMode: false
      };
    }
  };

  const layout = getLayoutConfig();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Brain size={32} />
            Dopemux Ultra UI
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Cognitive Intelligence Dashboard - Status: {cognitiveState.status.toUpperCase()}
          </Typography>
        </Box>

        {/* Cognitive State Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6} lg={3}>
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Zap color="#4caf50" size={24} />
              <Box>
                <Typography variant="h6">{(cognitiveState.energy * 100).toFixed(0)}%</Typography>
                <Typography variant="body2" color="text.secondary">Energy Level</Typography>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Eye color="#2196f3" size={24} />
              <Box>
                <Typography variant="h6">{(cognitiveState.attention * 100).toFixed(0)}%</Typography>
                <Typography variant="body2" color="text.secondary">Attention Focus</Typography>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Brain color="#ff9800" size={24} />
              <Box>
                <Typography variant="h6">{(cognitiveState.load * 100).toFixed(0)}%</Typography>
                <Typography variant="body2" color="text.secondary">Cognitive Load</Typography>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6} lg={3}>
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
              <TrendingUp color="#f44336" size={24} />
              <Box>
                <Typography variant="h6">
                  {cognitiveState.prediction ? (cognitiveState.prediction * 100).toFixed(0) + '%' : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">15-min Prediction</Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Main Dashboard */}
        <Grid container spacing={3}>
          {/* Cognitive Load Gauge - Always visible */}
          <Grid item xs={12} lg={layout.compactMode ? 12 : 4}>
            <CognitiveLoadGauge
              load={cognitiveState.load}
              status={cognitiveState.status}
              recommendation={cognitiveState.recommendation}
            />
          </Grid>

          {/* Task Sequencer */}
          <Grid item xs={12} lg={layout.compactMode ? 12 : 4}>
            <TaskSequencer cognitiveState={cognitiveState} />
          </Grid>

          {/* Prediction Panel */}
          {layout.showPredictions && (
            <Grid item xs={12} lg={4}>
              <PredictionPanel prediction={cognitiveState.prediction} />
            </Grid>
          )}

          {/* Team Dashboard */}
          {layout.showTeamDashboard && !isMobile && (
            <Grid item xs={12}>
              <TeamDashboard />
            </Grid>
          )}
        </Grid>

        {/* Footer */}
        <Box sx={{ mt: 4, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="body2" color="text.secondary" align="center">
            Ultra UI Dashboard - Adaptive Interface for Cognitive Optimization
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;