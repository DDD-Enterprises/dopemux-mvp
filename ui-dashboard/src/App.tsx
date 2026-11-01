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
  carryForecast,
  CognitiveReading,
  EMPTY_READING,
  isMessageObject,
  mapAggregateState,
  mapRealtimeState,
  remainingUpstreamSections,
  upstreamErrorSections,
} from './cognitiveReading';
import { dashboardApiHeaders, dashboardApiUrl, dashboardWsUrl } from './config';
import AttentionStatePanel from './components/AttentionStatePanel';
import LoadInstrument from './components/LoadInstrument';
import SignalFeed, { DashboardNotification } from './components/SignalFeed';
import TaskSequencer from './components/TaskSequencer';
import TeamDashboard from './components/TeamDashboard';
import RepositoryPlannerPage from './features/repository-planner/RepositoryPlannerPage';
import theme, { brandTokens, deriveStatus } from './theme';
import { asUtcIso, formatClockTime } from './time';

type SocketState = 'connecting' | 'open' | 'closed';
type ConnectionStatus = 'connecting' | 'live' | 'degraded';
// Where an error banner came from: only socket errors are cleared by a later good state_update.
type ErrorBanner = { source: 'socket' | 'task'; message: string };
// `upstreamSections` is set only for a GET that answered 200 with failed sections; transport failures leave it null.
type HttpError = { message: string; upstreamSections: string[] | null };

const STATE_ENDPOINT = `${dashboardApiUrl}/api/adhd-state`;
const SOCKET_ENDPOINT = `${dashboardWsUrl}/ws/state`;
const MAX_SIGNALS = 5;

const upstreamErrorMessage = (sections: string[]) =>
  `Failed: GET ${STATE_ENDPOINT} returned upstream errors for ${sections.join(', ')}.`;

// Brand: cyan = live, yellow = degraded or waiting. Red is reserved for failed/blocked.
const CONNECTION_META: Record<ConnectionStatus, { label: string; color: string }> = {
  live: { label: '[LIVE]', color: brandTokens.colors.ritualCyan },
  connecting: { label: '[CONNECTING]', color: brandTokens.colors.giltEdge },
  degraded: { label: '[DEGRADED]', color: brandTokens.colors.giltEdge },
};

const monoSx = { fontFamily: brandTokens.fonts.mono } as const;

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
  const [httpError, setHttpError] = useState<HttpError | null>(null);
  const [socketState, setSocketState] = useState<SocketState>('connecting');
  const [errorBanner, setErrorBanner] = useState<ErrorBanner | null>(null);
  const [retryTrigger, setRetryTrigger] = useState(0);
  const [showAllPanels, setShowAllPanels] = useState(false);
  const [isSipLogged, setIsSipLogged] = useState(false);
  const sipTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Once a live state_update lands, it is newer than any GET still in flight.
  const liveReadingSeenRef = useRef(false);
  // Latest reading, and when its forecast arrived (null = none), for the state_update merge.
  const readingRef = useRef<CognitiveReading>(EMPTY_READING);
  const forecastReceivedAtRef = useRef<number | null>(null);

  const handleRetry = useCallback(() => {
    liveReadingSeenRef.current = false;
    setHttpError(null);
    setSocketState('connecting');
    setErrorBanner(null);
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

  const reportSocketError = useCallback((message: string) => setErrorBanner({ source: 'socket', message }), []);
  const reportTaskError = useCallback((message: string) => setErrorBanner({ source: 'task', message }), []);

  const handleDismissNotification = useCallback((id: string) => {
    setNotifications((current) => current.filter((n) => n.id !== id));
  }, []);

  const handleClearNotifications = useCallback(() => setNotifications([]), []);

  // "Show all" lasts one critical episode: any non-critical reading re-arms the collapse.
  const applyReading = useCallback((next: CognitiveReading, forecastCarried = false) => {
    if (next.prediction === null) {
      forecastReceivedAtRef.current = null;
    } else if (!forecastCarried) {
      forecastReceivedAtRef.current = Date.now();
    }
    readingRef.current = next;
    setReading(next);
    setLastUpdated(new Date());
    if (next.load === null || deriveStatus(next.load) !== 'critical') {
      setShowAllPanels(false);
    }
  }, []);

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

    // Once a live state_update has landed, this GET is obsolete: neither its reading
    // nor its failure may replace what the socket already delivered.
    const isCurrent = () => isMounted && !liveReadingSeenRef.current;
    const fail = (message: string, upstreamSections: string[] | null = null) => {
      if (isCurrent()) {
        setHttpError({ message, upstreamSections });
      }
    };

    // Each failure stage gets its own message so the banner names what actually broke.
    async function loadInitialState() {
      let response: Response;
      try {
        response = await fetch(STATE_ENDPOINT, { headers: dashboardApiHeaders });
      } catch {
        fail(`Failed: GET ${STATE_ENDPOINT}, no response (network error).`);
        return;
      }
      if (!response.ok) {
        fail(`Failed: GET ${STATE_ENDPOINT} returned HTTP ${response.status}.`);
        return;
      }

      let payload: unknown;
      try {
        payload = await response.json();
      } catch {
        fail(`Failed: GET ${STATE_ENDPOINT} returned invalid JSON.`);
        return;
      }
      if (!isMessageObject(payload)) {
        fail(`Failed: GET ${STATE_ENDPOINT} returned an unexpected payload.`);
        return;
      }
      if (isCurrent()) {
        applyReading(mapAggregateState(payload));
        // HTTP 200 does not mean every upstream call worked: keep the partial reading, say what is missing.
        const failed = upstreamErrorSections(payload);
        if (failed.length > 0) {
          fail(upstreamErrorMessage(failed), failed);
        }
      }
    }

    void loadInitialState();

    return () => {
      isMounted = false;
    };
  }, [retryTrigger, applyReading]);

  useEffect(() => {
    const socket = new WebSocket(SOCKET_ENDPOINT);

    socket.onopen = () => {
      setSocketState('open');
    };

    socket.onmessage = (event) => {
      let message: unknown;
      try {
        message = JSON.parse(event.data);
      } catch {
        reportSocketError(`Failed: could not parse a message from ${SOCKET_ENDPOINT}.`);
        return;
      }
      if (!isMessageObject(message)) {
        reportSocketError(`Failed: unexpected message from ${SOCKET_ENDPOINT}.`);
        return;
      }

      // A state_update is a full snapshot: fields it omits become unknown, not stale, except
      // the forecast (never sent live), which carries over until it is 15 minutes old.
      // It supersedes an earlier GET failure: a transport one fully, an upstream-section one
      // only for the sections the snapshot now supplies.
      const snapshot = mapRealtimeState(message);
      if (snapshot) {
        const nextReading = carryForecast(
          snapshot,
          message,
          readingRef.current,
          forecastReceivedAtRef.current,
          Date.now()
        );
        liveReadingSeenRef.current = true;
        applyReading(nextReading, nextReading.prediction !== snapshot.prediction);
        setHttpError((current) => {
          if (current?.upstreamSections == null) {
            return null;
          }
          const remaining = remainingUpstreamSections(current.upstreamSections, nextReading);
          return remaining.length === 0
            ? null
            : { message: upstreamErrorMessage(remaining), upstreamSections: remaining };
        });
        // A good snapshot ends a socket problem, but not a clipboard or board failure.
        setErrorBanner((current) => (current?.source === 'socket' ? null : current));
        return;
      }
      if (message.type === 'state_update') {
        reportSocketError(`Failed: malformed state_update from ${SOCKET_ENDPOINT}.`);
        return;
      }

      if (message.type === 'dashboard_notification') {
        setNotifications((current) =>
          [
            {
              id: String(message.id || Date.now().toString() + Math.random().toString(36).substring(2, 9)),
              message: String(message.message || 'Notification received'),
              notificationType: String(message.notification_type || 'info'),
              timestamp: asUtcIso(String(message.timestamp || new Date().toISOString())),
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

    // Detach every handler first so a retired socket cannot touch state after a retry.
    return () => {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      socket.close();
    };
  }, [retryTrigger, applyReading, reportSocketError]);

  const status = reading.load === null ? null : deriveStatus(reading.load);
  const isCritical = status === 'critical' && !showAllPanels;
  const showTeamDashboard = !isMobile && (status === 'critical' ? showAllPanels : status !== 'high');

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
            sx={{ m: 0, fontFamily: brandTokens.fonts.display, fontWeight: 600, fontSize: '1.125rem', letterSpacing: '0.08em' }}
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
                {httpError.message}
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

        <Collapse in={errorBanner !== null} unmountOnExit>
          <Alert
            severity="error"
            icon={<AlertTriangle size={20} aria-hidden="true" />}
            onClose={() => setErrorBanner(null)}
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
            {errorBanner?.message}
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
            <TaskSequencer cognitiveState={{ status: status ?? 'unknown' }} onError={reportTaskError} />
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
                socketState={socketState}
                onDismiss={handleDismissNotification}
                onClear={handleClearNotifications}
              />
            </Grid>
          )}
          {showTeamDashboard && (
            <Grid item xs={12}>
              <TeamDashboard onError={reportTaskError} />
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
