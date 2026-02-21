import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  ThemeProvider,
  CssBaseline,
  Chip,
  Divider,
  useMediaQuery,
  useTheme
} from '@mui/material';
import { Brain, Zap, Eye, TrendingUp, Droplet } from 'lucide-react';
import theme, { brandTokens, statusStyles } from './theme';

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

function App() {
  const muiTheme = useTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));

  const [cognitiveState, setCognitiveState] = useState<CognitiveState>({
    energy: 0.7,
    attention: 0.6,
    load: 0.5,
    status: 'optimal',
    recommendation: 'Continue current work patterns'
  });

  // Connect to real-time data
  useEffect(() => {
    console.log("🔌 Connecting to ADHD Engine WebSocket...");
    const ws = new WebSocket('ws://localhost:8095/api/v1/ws/stream');

    ws.onopen = () => {
      console.log("✅ WebSocket Connected");
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'state_update') {
          const data = message.data;

          // Map backend string enums to numerical values for UI
          const energyMap: Record<string, number> = {
            'very_low': 0.2, 'low': 0.4, 'medium': 0.7, 'high': 0.9, 'hyperfocus': 1.0
          };

          const attentionMap: Record<string, number> = {
            'scattered': 0.3, 'transitioning': 0.5, 'focused': 0.8,
            'hyperfocused': 1.0, 'overwhelmed': 0.2
          };

          // Determine status based on cognitive load
          let status: CognitiveState['status'] = 'optimal';
          if (data.cognitive_load > 0.8) status = 'critical';
          else if (data.cognitive_load > 0.6) status = 'high';
          else if (data.cognitive_load < 0.3) status = 'low';

          setCognitiveState({
            energy: energyMap[data.energy_level] || 0.5,
            attention: attentionMap[data.attention_state] || 0.5,
            load: data.cognitive_load || 0.5,
            status: status,
            recommendation: data.recommendation || 'No active recommendation'
          });
        }
      } catch (err) {
        console.error("❌ Error parsing WebSocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("❌ WebSocket Error:", error);
    };

    return () => {
      ws.close();
    };
  }, []);

  // Adaptive layout based on cognitive load
  const getLayoutConfig = () => {
    if (cognitiveState.status === 'critical') {
      return {
        showTeamDashboard: false,
        showPredictions: false,
        compactMode: true
      };
    } else if (cognitiveState.status === 'high') {
      return {
        showTeamDashboard: false,
        showPredictions: true,
        compactMode: false
      };
    } else {
      return {
        showTeamDashboard: true,
        showPredictions: true,
        compactMode: false
      };
    }
  };

  const layout = getLayoutConfig();
  const statusMeta = statusStyles[cognitiveState.status];

  const metricCards = [
    {
      label: 'Energy Level',
      value: cognitiveState.energy,
      icon: <Zap color={brandTokens.colors.serumMint} size={24} />,
      roast: "You're sipping ambition like it's lukewarm coffee.",
    },
    {
      label: 'Attention Focus',
      value: cognitiveState.attention,
      icon: <Eye color={brandTokens.colors.ritualCyan} size={24} />,
      roast: "Focus is flirting with you; stop ghosting it.",
    },
    {
      label: 'Cognitive Load',
      value: cognitiveState.load,
      icon: <Brain color={brandTokens.colors.saintGold} size={24} />,
      roast: "Load creeping up like a brat testing limits.",
    },
    {
      label: '15-min Prediction',
      value: cognitiveState.prediction ?? null,
      icon: <TrendingUp color={brandTokens.colors.giltEdge} size={24} />,
      roast: "Future you is pacing. Hydrate before they mutiny.",
    },
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box
          sx={{
            mb: 4,
            p: 3,
            borderRadius: 4,
            background: brandTokens.gradients.velvet,
            border: `1px solid rgba(148, 250, 219, 0.35)`,
            boxShadow: '0 30px 80px rgba(2, 6, 23, 0.6)',
          }}
        >
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 2, mb: 2 }}>
            <Chip
              label={`${brandTokens.chips.live} DØPEMÜX Ritual Daemon`}
              className="dopemux-chip"
              color="primary"
            />
            <Chip
              label={`${brandTokens.chips.consent}`}
              className="dopemux-chip"
              variant="outlined"
              sx={{ borderColor: 'rgba(255, 207, 120, 0.9)', color: brandTokens.colors.saintGold }}
            />
            <Chip
              icon={<Droplet size={16} color={brandTokens.colors.aftercareViolet} />}
              label="[AFTERCARE] Logged. Hydrate."
              className="dopemux-chip"
              sx={{ borderColor: 'rgba(155, 120, 255, 0.8)', color: brandTokens.colors.aftercareViolet }}
            />
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 600, mb: 1, letterSpacing: '0.08em' }}>
            Dopemux Ultra UI
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 720 }}>
            Luxury filth meets lab precision. I track your cognitive drips, roast your sprint sins,
            and still remind you to hydrate. Status: <strong>{brandTokens.chips.live}</strong> {statusMeta.label}.
          </Typography>
          <Divider sx={{ my: 2, borderColor: 'rgba(125, 251, 246, 0.3)' }} />
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              label={`${statusMeta.label} • ${(cognitiveState.load * 100).toFixed(0)}% load`}
              sx={{
                backgroundColor: `${statusMeta.color}1A`,
                color: statusMeta.color,
                border: `1px solid ${statusMeta.color}`,
              }}
            />
            <Chip
              label={`Recommendation: ${cognitiveState.recommendation}`}
              sx={{
                backgroundColor: 'rgba(32, 50, 72, 0.65)',
                color: brandTokens.colors.serumMint,
                border: '1px solid rgba(148, 250, 219, 0.35)',
              }}
            />
          </Box>
        </Box>

        <Grid container spacing={3} sx={{ mb: 3 }}>
          {metricCards.map((metric) => (
            <Grid item xs={12} md={6} lg={3} key={metric.label}>
              <Paper
                sx={{
                  p: 2.5,
                  minHeight: 140,
                  borderRadius: 3,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1.2,
                  border: `1px solid rgba(255,255,255,0.08)`,
                  background: 'linear-gradient(135deg, rgba(4,22,40,0.9), rgba(10,10,26,0.9))',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  {metric.icon}
                  <Box>
                    <Typography variant="h6">{metric.value !== null ? `${(metric.value * 100).toFixed(0)}%` : 'N/A'}</Typography>
                    <Typography variant="body2" color="text.secondary">{metric.label}</Typography>
                  </Box>
                </Box>
                <Typography className="dopemux-roast">{metric.roast}</Typography>
                <Typography className="dopemux-aftercare">Logged. Hydrate.</Typography>
              </Paper>
            </Grid>
          ))}
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
