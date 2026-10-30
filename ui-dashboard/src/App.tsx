import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Collapse,
  Container,
  CssBaseline,
  Grid,
  Link,
  ThemeProvider,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { AlertTriangle } from 'lucide-react';

import {
  AggregateDashboardState,
  CognitiveReading,
  EMPTY_READING,
  mapAggregateState,
  mapRealtimeState,
} from './cognitiveReading';
import { dashboardApiHeaders, dashboardApiUrl, dashboardWsUrl } from './config';
import AttentionStatePanel from './components/AttentionStatePanel';
import LoadInstrument from './components/LoadInstrument';
import SignalFeed, { DashboardNotification } from './components/SignalFeed';
import TaskSequencer from './components/TaskSequencer';
import TeamDashboard from './components/TeamDashboard';
import RepositoryPlannerPage from './features/repository-planner/RepositoryPlannerPage';
import theme, { brandTokens, deriveStatus } from './theme';
import { formatClockTime } from './time';

type SocketState = 'connecting' | 'open' | 'closed';
type ConnectionStatus = 'connecting' | 'live' | 'degraded';

const STATE_ENDPOINT = `${dashboardApiUrl}/api/adhd-state`;
const SOCKET_ENDPOINT = `${dashboardWsUrl}/ws/state`;
const MAX_SIGNALS = 5;

// Brand: cyan = live, yellow = degraded or waiting. Red is reserved for failed/blocked.
const CONNECTION_META: Record<ConnectionStatus, { label: string; color: string }> = {
  live: { label: '[LIVE]', color: brandTokens.colors.ritualCyan },
  connecting: { label: '[CONNECTING]', color: brandTokens.colors.giltEdge },
  degraded: { label: '[DEGRADED]', color: brandTokens.colors.giltEdge },
};

const monoSx = { fontFamily: '"JetBrains Mono", monospace' } as const;

// String lengths on purpose: in MUI sx a bare `1` means 100%.
const visuallyHiddenSx = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  margin: '-1px',
  padding: 0,
  border: 0,
  overflow: 'hidden',
  clip: 'rect(0 0 0 0)',
  whiteSpace: 'nowrap',
} as const;

function endpointHost(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

function DashboardApp() {
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [reading, setReading] = useState<CognitiveReading>(EMPTY_READING);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [notifications, setNotifications] = useState<DashboardNotification[]>([]);
  const [httpError, setHttpError] = useState<string | null>(null);
  const [socketState, setSocketState] = useState<SocketState>('connecting');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [retryTrigger, setRetryTrigger] = useState(0);
  const [showAllPanels, setShowAllPanels] = useState(false);
  const [isSipLogged, setIsSipLogged] = useState(false);
  const sipTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleRetry = useCallback(() => {
    setHttpError(null);
    setSocketState('connecting');
    setErrorMessage(null);
    setRetryTrigger((prev) => prev + 1);
  }, []);

  const handleLogSip = useCallback(() => {
    setIsSipLogged(true);
    if (sipTimeoutRef.current) {
      clearTimeout(sipTimeoutRef.current);
    }
    sipTimeoutRef.current = setTimeout(() => {
      setIsSipLogged(false);
      sipTimeoutRef.current = null;
    }, 2000);
  }, []);

  const handleDismissNotification = useCallback((id: string) => {
    setNotifications((current) => current.filter((n) => n.id !== id));
  }, []);

  const handleClearNotifications = useCallback(() => setNotifications([]), []);

  useEffect(() => {
    return () => {
      if (sipTimeoutRef.current) {
        clearTimeout(sipTimeoutRef.current);
        sipTimeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadInitialState() {
      try {
        const response = await fetch(STATE_ENDPOINT, { headers: dashboardApiHeaders });
        if (!isMounted) {
          return;
        }
        if (!response.ok) {
          setHttpError(`Failed: GET ${STATE_ENDPOINT} returned HTTP ${response.status}.`);
          return;
        }
        const payload = (await response.json()) as AggregateDashboardState;
        if (!isMounted) {
          return;
        }
        setReading(mapAggregateState(payload));
        setLastUpdated(new Date());
      } catch {
        if (isMounted) {
          setHttpError(`Failed: GET ${STATE_ENDPOINT}, no response (network error).`);
        }
      }
    }

    void loadInitialState();

    return () => {
      isMounted = false;
    };
  }, [retryTrigger]);

  useEffect(() => {
    const socket = new WebSocket(SOCKET_ENDPOINT);

    socket.onopen = () => {
      setSocketState('open');
    };

    socket.onmessage = (event) => {
      let message: Record<string, unknown>;
      try {
        message = JSON.parse(event.data) as Record<string, unknown>;
      } catch {
        setErrorMessage(`Failed: could not parse a message from ${SOCKET_ENDPOINT}.`);
        return;
      }

      // A state_update is a full snapshot: fields it omits become unknown, not stale.
      const nextReading = mapRealtimeState(message);
      if (nextReading) {
        setReading(nextReading);
        setLastUpdated(new Date());
        return;
      }

      if (message.type === 'dashboard_notification') {
        setNotifications((current) =>
          [
            {
              id: String(message.id || Date.now().toString() + Math.random().toString(36).substring(2, 9)),
              message: String(message.message || 'Notification received'),
              notificationType: String(message.notification_type || 'info'),
              timestamp: String(message.timestamp || new Date().toISOString()),
            },
            ...current,
          ].slice(0, MAX_SIGNALS)
        );
      }
    };

    socket.onerror = () => {
      setSocketState('closed');
    };

    socket.onclose = () => {
      setSocketState('closed');
    };

    return () => {
      socket.onerror = null;
      socket.onclose = null;
      socket.close();
    };
  }, [retryTrigger]);

  const status = reading.load === null ? null : deriveStatus(reading.load);
  const isCritical = status === 'critical' && !showAllPanels;
  const showTeamDashboard = status !== 'critical' && status !== 'high' && !isMobile;

  const connectionStatus: ConnectionStatus =
    socketState === 'open' ? 'live' : socketState === 'connecting' && !httpError ? 'connecting' : 'degraded';
  const connection = CONNECTION_META[connectionStatus];

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
          '&:focus-visible': {
            top: 0,
            outline: `2px solid ${brandTokens.text.primary}`,
          },
        }}
      >
        Skip to main content
      </Link>
      <Container maxWidth="xl" sx={{ py: 2.5, display: 'flex', flexDirection: 'column', gap: 2.5 }}>
        <Box
          component="header"
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '12px 20px',
            px: 2,
            py: 1.5,
            border: `1px solid ${brandTokens.borders.subtle}`,
            borderRadius: '12px',
            bgcolor: alpha(brandTokens.colors.voidNavy, 0.6),
          }}
        >
          <Typography
            component="h1"
            sx={{ m: 0, fontFamily: '"Space Grotesk", sans-serif', fontWeight: 600, fontSize: '1.125rem', letterSpacing: '0.08em' }}
          >
            DØPEMÜX
            <Box component="span" sx={visuallyHiddenSx}>
              {' '}cockpit
            </Box>
          </Typography>
          <Box
            role="status"
            aria-label={`Connection ${connectionStatus}`}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1,
              px: 1.25,
              py: 0.5,
              border: `1px solid ${alpha(connection.color, 0.6)}`,
              borderRadius: '999px',
              ...monoSx,
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.08em',
              color: connection.color,
            }}
          >
            <Box aria-hidden="true" sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: connection.color }} />
            {connection.label}
          </Box>
          <Typography sx={{ ...monoSx, fontSize: '0.8125rem', color: brandTokens.text.secondary }}>
            {`adhd-dashboard ${endpointHost(dashboardApiUrl)}`}
          </Typography>
          <Typography sx={{ ...monoSx, fontSize: '0.8125rem', color: brandTokens.text.muted }}>
            {lastUpdated ? `updated ${formatClockTime(lastUpdated)}` : 'no update received'}
          </Typography>
          <Typography sx={{ ...monoSx, fontSize: '0.75rem', letterSpacing: '0.08em', color: brandTokens.text.muted }}>
            [CONSENT: UNKNOWN]
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title="Local reminder only. Nothing is saved." arrow describeChild>
            <Button
              variant="outlined"
              onClick={handleLogSip}
              sx={{
                minHeight: 40,
                ...monoSx,
                fontSize: '0.75rem',
                borderColor: alpha(brandTokens.colors.aftercareViolet, 0.7),
                color: brandTokens.colors.aftercareViolet,
                '&:hover': {
                  borderColor: brandTokens.colors.aftercareViolet,
                  bgcolor: alpha(brandTokens.colors.aftercareViolet, 0.08),
                },
              }}
            >
              {isSipLogged ? '[AFTERCARE] Sip logged' : '[AFTERCARE] Log a sip'}
            </Button>
          </Tooltip>
        </Box>

        {(httpError !== null || socketState === 'closed') && (
          <Alert
            severity="warning"
            icon={<AlertTriangle size={20} aria-hidden="true" />}
            action={
              <Button color="inherit" variant="outlined" onClick={handleRetry} sx={{ minHeight: 40 }}>
                Retry
              </Button>
            }
            sx={{
              alignItems: 'center',
              borderRadius: '12px',
              color: brandTokens.text.primary,
              backgroundColor: alpha(brandTokens.colors.giltEdge, 0.06),
              border: `1px solid ${alpha(brandTokens.colors.giltEdge, 0.55)}`,
              '& .MuiAlert-icon': { color: brandTokens.colors.giltEdge },
              '& .MuiAlert-action': { color: brandTokens.colors.giltEdge },
            }}
          >
            {httpError && (
              <Typography sx={{ ...monoSx, fontSize: '0.875rem', fontWeight: 600, color: brandTokens.colors.giltEdge }}>
                {httpError}
              </Typography>
            )}
            {socketState === 'closed' && (
              <Typography sx={{ ...monoSx, fontSize: '0.875rem', fontWeight: 600, color: brandTokens.colors.giltEdge }}>
                {`Failed: WebSocket ${SOCKET_ENDPOINT} closed. Live updates stopped.`}
              </Typography>
            )}
            <Typography sx={{ fontSize: '0.9375rem' }}>
              {lastUpdated
                ? `Values shown are from ${formatClockTime(lastUpdated)}.`
                : 'Load, energy and attention are unknown until the service responds.'}
            </Typography>
            <Typography sx={{ fontSize: '0.9375rem', color: brandTokens.text.secondary }}>
              {`Next: check that the adhd-dashboard service is running at ${dashboardApiUrl}, then retry.`}
            </Typography>
          </Alert>
        )}

        <Collapse in={Boolean(errorMessage)} unmountOnExit>
          <Alert
            severity="error"
            icon={<AlertTriangle size={20} aria-hidden="true" />}
            onClose={() => setErrorMessage(null)}
            closeText="Dismiss error notification"
            slotProps={{
              closeButton: {
                'aria-label': 'Dismiss error notification',
              },
            }}
            sx={{
              borderRadius: '12px',
              backgroundColor: alpha(brandTokens.colors.errorRed, 0.08),
              border: `1px solid ${brandTokens.colors.errorRed}`,
            }}
          >
            {errorMessage}
          </Alert>
        </Collapse>

        <Grid container spacing={2.5} id="main-dashboard" component="main" tabIndex={-1} sx={{ outline: 'none' }}>
          <Grid item xs={12} lg={5} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <LoadInstrument load={reading.load} prediction={reading.prediction} recommendation={reading.recommendation} />
            {!isCritical && (
              <AttentionStatePanel energyLevel={reading.energyLevel} attentionState={reading.attentionState} />
            )}
          </Grid>
          <Grid item xs={12} lg={7}>
            <TaskSequencer cognitiveState={{ status: status ?? 'unknown' }} onError={setErrorMessage} />
          </Grid>
          {isCritical ? (
            <Grid item xs={12}>
              <Box
                sx={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  gap: 1.5,
                  px: 2,
                  py: 1.5,
                  border: `1px dashed ${brandTokens.borders.strong}`,
                  borderRadius: '12px',
                }}
              >
                <Typography sx={{ ...monoSx, flex: '1 1 320px', fontSize: '0.8125rem', color: brandTokens.text.secondary }}>
                  Hidden while load is critical: attention state, signal feed, team board.
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setShowAllPanels(true)}
                  aria-label="Show all panels"
                  sx={{ minHeight: 40, borderColor: brandTokens.borders.strong, color: brandTokens.text.secondary }}
                >
                  Show all
                </Button>
              </Box>
            </Grid>
          ) : (
            <Grid item xs={12}>
              <SignalFeed
                notifications={notifications}
                socketUrl={SOCKET_ENDPOINT}
                isListening={socketState === 'open'}
                onDismiss={handleDismissNotification}
                onClear={handleClearNotifications}
              />
            </Grid>
          )}
          {showTeamDashboard && (
            <Grid item xs={12}>
              <TeamDashboard onError={setErrorMessage} />
            </Grid>
          )}
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

function App() {
  return window.location.pathname === '/repository-planner' ? <RepositoryPlannerPage /> : <DashboardApp />;
}

export default App;
