import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Collapse,
  Container,
  Fade,
  CssBaseline,
  Divider,
  Grid,
  IconButton,
  Link,
  Paper,
  ThemeProvider,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Bell, Brain, Droplet, Eye, Trash2, TrendingUp, Zap } from 'lucide-react';

import { dashboardApiHeaders, dashboardApiUrl, dashboardWsUrl } from './config';
import CognitiveLoadGauge from './components/CognitiveLoadGauge';
import { getNotificationColor } from './notificationColors';
import PredictionPanel from './components/PredictionPanel';
import TaskSequencer from './components/TaskSequencer';
import TeamDashboard from './components/TeamDashboard';
import theme, { brandTokens, statusStyles } from './theme';

interface CognitiveState {
  energy: number;
  attention: number;
  load: number;
  prediction?: number;
  status: 'low' | 'optimal' | 'high' | 'critical';
  recommendation: string;
}

interface Notification {
  message: string;
  notificationType: string;
  timestamp: string;
}

interface AggregateDashboardState {
  energy?: {
    energy_level?: string;
  };
  attention?: {
    attention_state?: string;
  };
  cognitive_load?: {
    cognitive_load?: number;
    predicted_load_15min?: number;
  };
  recommendation?: string;
}

const energyMap: Record<string, number> = {
  very_low: 0.2,
  low: 0.4,
  medium: 0.7,
  high: 0.9,
  hyperfocus: 1.0,
};

const attentionMap: Record<string, number> = {
  scattered: 0.3,
  transitioning: 0.5,
  focused: 0.8,
  hyperfocused: 1.0,
  overwhelmed: 0.2,
};

function deriveStatus(load: number): CognitiveState['status'] {
  if (load > 0.8) {
    return 'critical';
  }
  if (load > 0.6) {
    return 'high';
  }
  if (load < 0.3) {
    return 'low';
  }
  return 'optimal';
}

function mapAggregateState(payload: AggregateDashboardState): CognitiveState {
  const load = payload.cognitive_load?.cognitive_load ?? 0.5;
  return {
    energy: energyMap[payload.energy?.energy_level || 'medium'] || 0.5,
    attention: attentionMap[payload.attention?.attention_state || 'focused'] || 0.5,
    load,
    prediction: payload.cognitive_load?.predicted_load_15min,
    status: deriveStatus(load),
    recommendation: payload.recommendation || 'No active recommendation',
  };
}

function mapRealtimeState(message: Record<string, unknown>): CognitiveState | null {
  if (message.type !== 'state_update') {
    return null;
  }

  const data = (message.data || {}) as Record<string, unknown>;
  const load = typeof data.cognitive_load === 'number' ? data.cognitive_load : 0.5;

  return {
    energy: energyMap[String(data.energy_level || 'medium')] || 0.5,
    attention: attentionMap[String(data.attention_state || 'focused')] || 0.5,
    load,
    prediction: typeof data.predicted_load_15min === 'number' ? data.predicted_load_15min : undefined,
    status: deriveStatus(load),
    recommendation: String(data.recommendation || 'No active recommendation'),
  };
}

const formatTimestamp = (dateStr: string) => {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '[--:--:--]';
  const hh = date.getHours().toString().padStart(2, '0');
  const mm = date.getMinutes().toString().padStart(2, '0');
  const ss = date.getSeconds().toString().padStart(2, '0');
  return `[${hh}:${mm}:${ss}]`;
};

function App() {
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const feedHeadingRef = useRef<HTMLHeadingElement>(null);
  const [cognitiveState, setCognitiveState] = useState<CognitiveState>({
    energy: 0.7,
    attention: 0.6,
    load: 0.5,
    status: 'optimal',
    recommendation: 'Continue current work patterns',
  });
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'live' | 'degraded'>('connecting');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadInitialState() {
      try {
        const response = await fetch(`${dashboardApiUrl}/api/adhd-state`, {
          headers: dashboardApiHeaders,
        });
        if (!response.ok) {
          throw new Error(`Dashboard state request failed with ${response.status}`);
        }

        const payload = (await response.json()) as AggregateDashboardState;
        if (!isMounted) {
          return;
        }
        setCognitiveState(mapAggregateState(payload));
        setConnectionStatus('live');
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setConnectionStatus('degraded');
        setErrorMessage(error instanceof Error ? error.message : 'Unable to load dashboard state');
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadInitialState();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const socket = new WebSocket(`${dashboardWsUrl}/ws/state`);

    socket.onopen = () => {
      setConnectionStatus('live');
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as Record<string, unknown>;
        const nextState = mapRealtimeState(message);

        if (nextState) {
          setCognitiveState((current) => ({ ...current, ...nextState }));
          return;
        }

        if (message.type === 'dashboard_notification') {
          setNotifications((current) => [
            {
              message: String(message.message || 'Notification received'),
              notificationType: String(message.notification_type || 'info'),
              timestamp: String(message.timestamp || new Date().toISOString()),
            },
            ...current,
          ].slice(0, 5));
        }
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'WebSocket parse failure');
      }
    };

    socket.onerror = () => {
      setConnectionStatus('degraded');
    };

    socket.onclose = () => {
      setConnectionStatus((current) => (current === 'live' ? 'degraded' : current));
    };

    return () => {
      socket.close();
    };
  }, []);

  const layout =
    cognitiveState.status === 'critical'
      ? { showTeamDashboard: false, showPredictions: false, compactMode: true }
      : cognitiveState.status === 'high'
        ? { showTeamDashboard: false, showPredictions: true, compactMode: false }
        : { showTeamDashboard: true, showPredictions: true, compactMode: false };

  const statusMeta = statusStyles[cognitiveState.status];
  const connectionLabel =
    connectionStatus === 'live'
      ? brandTokens.chips.live
      : connectionStatus === 'connecting'
        ? brandTokens.chips.connecting
        : brandTokens.chips.degraded;

  const connectionColor =
    connectionStatus === 'live'
      ? brandTokens.colors.ritualCyan
      : connectionStatus === 'connecting'
        ? brandTokens.colors.saintGold
        : brandTokens.colors.gremlinPink;

  const metricCards = [
    {
      label: 'Energy Level',
      value: cognitiveState.energy,
      icon: <Zap color={brandTokens.colors.serumMint} size={24} aria-hidden="true" />,
      roast: "You're sipping ambition like it's lukewarm coffee.",
      tooltip: 'Your current biometric energy reserve based on activity and sleep data',
    },
    {
      label: 'Attention Focus',
      value: cognitiveState.attention,
      icon: <Eye color={brandTokens.colors.ritualCyan} size={24} aria-hidden="true" />,
      roast: 'Focus is flirting with you; stop ghosting it.',
      tooltip: 'Real-time attention state: scattered, focused, or hyperfocused',
    },
    {
      label: 'Cognitive Load',
      value: cognitiveState.load,
      icon: <Brain color={brandTokens.colors.saintGold} size={24} aria-hidden="true" />,
      roast: 'Load creeping up like a brat testing limits.',
      tooltip: 'Total mental effort being exerted on current tasks',
    },
    {
      label: '15-min Prediction',
      value: cognitiveState.prediction ?? null,
      icon: <TrendingUp color={brandTokens.colors.giltEdge} size={24} aria-hidden="true" />,
      roast: 'Future you is pacing. Hydrate before they mutiny.',
      tooltip: 'AI-driven forecast of your cognitive state for the next 15 minutes',
    },
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Link
        href="#main-dashboard"
        sx={{
          position: 'absolute',
          top: -100,
          left: 0,
          backgroundColor: brandTokens.colors.serumMint,
          color: brandTokens.colors.inkBlack,
          padding: '8px 16px',
          zIndex: 9999,
          borderRadius: '0 0 4px 0',
          fontWeight: 'bold',
          textDecoration: 'none',
          transition: 'top 0.2s',
          '&:focus-visible': {
            top: 0,
            outline: `2px solid ${brandTokens.text.primary}`,
          },
        }}
      >
        Skip to main content
      </Link>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box
          component="header"
          sx={{
            mb: 4,
            p: 3,
            borderRadius: 4,
            background: brandTokens.gradients.velvet,
            border: `1px solid ${brandTokens.borders.mint}`,
            boxShadow: brandTokens.shadows.panel,
          }}
        >
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 2, mb: 2 }}>
            <Tooltip title="Real-time connection to the ADHD dashboard surface" arrow>
              <Chip
                icon={
                  <Box
                    aria-hidden="true"
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: connectionColor,
                      ml: 1,
                      animation: 'pulse 2s infinite',
                      '@keyframes pulse': {
                        '0%': { boxShadow: `0 0 0 0px ${alpha(connectionColor, 0.7)}` },
                        '70%': { boxShadow: `0 0 0 8px ${alpha(connectionColor, 0)}` },
                        '100%': { boxShadow: `0 0 0 0px ${alpha(connectionColor, 0)}` },
                      },
                    }}
                  />
                }
                label={`${connectionLabel} DØPEMÜX Ritual Daemon`}
                aria-label={`System is actively monitoring ritual state: ${connectionLabel} DØPEMÜX Ritual Daemon`}
                className="dopemux-chip"
                color={
                  connectionStatus === 'live'
                    ? 'primary'
                    : connectionStatus === 'connecting'
                      ? 'secondary'
                      : 'error'
                }
                tabIndex={0}
              />
            </Tooltip>
            <Tooltip title="User consent verified for cognitive monitoring" arrow>
              <Chip
                label={`${brandTokens.chips.consent}`}
                aria-label="User consent verified for cognitive monitoring"
                className="dopemux-chip"
                variant="outlined"
                sx={{ borderColor: alpha(brandTokens.colors.saintGold, 0.9), color: brandTokens.colors.saintGold }}
                tabIndex={0}
              />
            </Tooltip>
            <Tooltip title="Health and hydration status" arrow>
              <Chip
                icon={<Droplet size={16} color={brandTokens.colors.aftercareViolet} />}
                label="[AFTERCARE] Logged. Hydrate."
                aria-label="Health and hydration status: [AFTERCARE] Logged. Hydrate."
                className="dopemux-chip"
                sx={{ borderColor: alpha(brandTokens.colors.aftercareViolet, 0.8), color: brandTokens.colors.aftercareViolet }}
                tabIndex={0}
              />
            </Tooltip>
          </Box>
          <Typography variant="h2" sx={{ fontWeight: 600, mb: 1, letterSpacing: '0.08em' }}>
            Dopemux Ultra UI
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 720 }}>
            Luxury filth meets lab precision. I track your cognitive drips, roast your sprint sins,
            and still remind you to hydrate. Status: <strong>{connectionLabel}</strong> {statusMeta.label}.
          </Typography>
          <Divider sx={{ my: 2, borderColor: brandTokens.borders.cyan }} />
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Tooltip title="Current cognitive status and load percentage" arrow>
              <Chip
                label={`${statusMeta.label} • ${(cognitiveState.load * 100).toFixed(0)}% load`}
                aria-label={`Current status: ${statusMeta.label}, ${(cognitiveState.load * 100).toFixed(0)}% cognitive load`}
                tabIndex={0}
                sx={{
                  backgroundColor: alpha(statusMeta.color, 0.1),
                  color: statusMeta.color,
                  border: `1px solid ${statusMeta.color}`,
                }}
              />
            </Tooltip>
            <Tooltip title="AI-generated recommendation based on current load" arrow>
              <Chip
                label={`Recommendation: ${cognitiveState.recommendation}`}
                aria-label={`AI Recommendation: ${cognitiveState.recommendation}`}
                tabIndex={0}
                sx={{
                  backgroundColor: alpha(brandTokens.colors.voidNavy, 0.65),
                  color: brandTokens.colors.serumMint,
                  border: `1px solid ${brandTokens.borders.mint}`,
                }}
              />
            </Tooltip>
          </Box>
        </Box>

        <Collapse in={Boolean(errorMessage)}>
          <Alert
            severity="error"
            onClose={() => setErrorMessage(null)}
            sx={{
              mb: 3,
              borderRadius: 3,
              backgroundColor: alpha(brandTokens.colors.gremlinPink, 0.08),
              border: `1px solid ${brandTokens.colors.gremlinPink}`,
            }}
          >
            {errorMessage}
          </Alert>
        </Collapse>

        <Grid container spacing={3} sx={{ mb: 3 }}>
          {metricCards.map((metric) => (
            <Grid item xs={12} md={6} lg={3} key={metric.label}>
              <Tooltip title={metric.tooltip} arrow>
                <Paper
                  tabIndex={0}
                  aria-label={`${metric.label}: ${metric.value !== null ? (metric.value * 100).toFixed(0) : 'N/A'}%`}
                  sx={{
                    p: 2.5,
                    minHeight: 140,
                    borderRadius: 3,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 1.2,
                    border: `1px solid ${brandTokens.borders.subtle}`,
                    background: brandTokens.gradients.focusCard,
                    cursor: 'help',
                    outline: 'none',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover, &:focus-visible': {
                      borderColor: brandTokens.colors.ritualCyan,
                      transform: 'translateY(-4px)',
                      boxShadow: `0 0 20px ${alpha(brandTokens.colors.ritualCyan, 0.2)}`,
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {metric.icon}
                    </Box>
                    <Box>
                      <Typography variant="h6">
                        {metric.value !== null ? `${(metric.value * 100).toFixed(0)}%` : 'N/A'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">{metric.label}</Typography>
                    </Box>
                  </Box>
                  <Typography className="dopemux-roast">{metric.roast}</Typography>
                  <Typography className="dopemux-aftercare">Logged. Hydrate.</Typography>
                </Paper>
              </Tooltip>
            </Grid>
          ))}
        </Grid>

        <Paper
          sx={{
            mb: 3,
            p: 2.5,
            borderRadius: 3,
            border: `1px solid ${brandTokens.borders.subtle}`,
            background: brandTokens.gradients.focusCard,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
            <Bell size={18} aria-hidden="true" />
            <Typography
              variant="h6"
              ref={feedHeadingRef}
              tabIndex={-1}
              sx={{ outline: 'none' }}
            >
              Live Signal Feed
            </Typography>
            {isLoading && (
              <CircularProgress
                size={16}
                sx={{ ml: 'auto' }}
                aria-label="Loading updates"
              />
            )}
            {notifications.length > 0 && (
              <Tooltip title="Clear all notifications to reduce visual noise" arrow>
                <Chip
                  size="small"
                  variant="outlined"
                  icon={<Trash2 size={14} aria-hidden="true" />}
                  label="Clear"
                  onClick={() => {
                    setNotifications([]);
                    feedHeadingRef.current?.focus();
                  }}
                  aria-label="Clear all notifications"
                  sx={{
                    ml: isLoading ? 1 : 'auto',
                    cursor: 'pointer',
                    bgcolor: alpha(brandTokens.colors.gremlinPink, 0.1),
                    color: brandTokens.colors.gremlinPink,
                    borderColor: brandTokens.colors.gremlinPink,
                    '&:hover': {
                      bgcolor: alpha(brandTokens.colors.gremlinPink, 0.2),
                    },
                  }}
                />
              </Tooltip>
            )}
          </Box>
          {notifications.length > 0 ? (
            <Box
              sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}
              role="log"
              aria-live="polite"
            >
              {notifications.map((notification) => {
                const severityColor = getNotificationColor(notification.notificationType);
                return (
                  <Fade in={true} key={`${notification.timestamp}-${notification.message}`}>
                    <Chip
                      label={`${formatTimestamp(notification.timestamp)} ${notification.notificationType}: ${notification.message}`}
                      variant="outlined"
                      sx={{
                        maxWidth: '100%',
                        borderColor: alpha(severityColor, 0.6),
                        color: severityColor,
                        backgroundColor: alpha(severityColor, 0.08),
                      }}
                    />
                  </Fade>
                );
              })}
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Typography variant="body2" color="text.secondary">
                Listening for ConPort and ADHD event traffic
              </Typography>
              <Box
                aria-hidden="true"
                sx={{
                  display: 'flex',
                  gap: 0.5,
                  '& span': {
                    width: 4,
                    height: 4,
                    borderRadius: '50%',
                    bgcolor: brandTokens.colors.ritualCyan,
                    animation: 'listeningPulse 1.4s infinite ease-in-out both',
                  },
                  '& span:nth-of-type(1)': { animationDelay: '-0.32s' },
                  '& span:nth-of-type(2)': { animationDelay: '-0.16s' },
                  '@keyframes listeningPulse': {
                    '0%, 80%, 100%': { transform: 'scale(0)' },
                    '40%': { transform: 'scale(1.0)' },
                  },
                }}
              >
                <span />
                <span />
                <span />
              </Box>
            </Box>
          )}
        </Paper>

        <Grid
          container
          spacing={3}
          id="main-dashboard"
          component="main"
          tabIndex={-1}
          sx={{ outline: 'none' }}
        >
          <Grid item xs={12} lg={layout.compactMode ? 12 : 4}>
            <CognitiveLoadGauge
              load={cognitiveState.load}
              status={cognitiveState.status}
              recommendation={cognitiveState.recommendation}
            />
          </Grid>
          <Grid item xs={12} lg={layout.compactMode ? 12 : 4}>
            <TaskSequencer cognitiveState={cognitiveState} />
          </Grid>
          {layout.showPredictions && (
            <Grid item xs={12} lg={4}>
              <PredictionPanel prediction={cognitiveState.prediction} />
            </Grid>
          )}
          {layout.showTeamDashboard && !isMobile && (
            <Grid item xs={12}>
              <TeamDashboard />
            </Grid>
          )}
        </Grid>

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
