import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Button, IconButton, Paper, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { X } from 'lucide-react';

import { getNotificationColor } from '../notificationColors';
import { brandTokens } from '../theme';
import { formatClockTime } from '../time';

export interface DashboardNotification {
  id: string;
  message: string;
  notificationType: string;
  timestamp: string;
}

interface SignalFeedProps {
  notifications: DashboardNotification[];
  socketUrl: string;
  socketState: 'connecting' | 'open' | 'closed';
  onDismiss: (id: string) => void;
  onClear: () => void;
}

const EMPTY_FEED_TEXT = {
  open: (url: string) => `No signals received yet. Listening on ${url}.`,
  connecting: (url: string) => `Connecting to ${url}.`,
  closed: (url: string) => `No signals received. Socket ${url} is closed.`,
};

const monoSx = { fontFamily: brandTokens.fonts.mono } as const;

const SignalFeed: React.FC<SignalFeedProps> = ({ notifications, socketUrl, socketState, onDismiss, onClear }) => {
  const isListening = socketState === 'open';
  const headingRef = useRef<HTMLHeadingElement>(null);
  const confirmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isConfirmingClear, setIsConfirmingClear] = useState(false);

  const cancelConfirm = useCallback(() => {
    if (confirmTimeoutRef.current) {
      clearTimeout(confirmTimeoutRef.current);
      confirmTimeoutRef.current = null;
    }
    setIsConfirmingClear(false);
  }, []);

  useEffect(() => cancelConfirm, [cancelConfirm]);

  const handleClear = () => {
    if (!isConfirmingClear) {
      setIsConfirmingClear(true);
      confirmTimeoutRef.current = setTimeout(() => {
        setIsConfirmingClear(false);
        confirmTimeoutRef.current = null;
      }, 5000);
      return;
    }
    cancelConfirm();
    onClear();
    headingRef.current?.focus();
  };

  const latest = notifications[0];

  return (
    <Paper
      component="section"
      aria-labelledby="signal-feed-title"
      sx={{ p: 3, borderRadius: '18px', display: 'flex', flexDirection: 'column', gap: 1.5 }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
        <Typography
          id="signal-feed-title"
          ref={headingRef}
          tabIndex={-1}
          component="h2"
          sx={{
            ...monoSx,
            fontSize: '0.75rem',
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: brandTokens.text.secondary,
            outline: 'none',
          }}
        >
          Signal Feed
        </Typography>
        {isListening && (
          <Box
            aria-hidden="true"
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              bgcolor: brandTokens.colors.ritualCyan,
              animation: 'feed-listening 2s ease-in-out infinite',
              '@keyframes feed-listening': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.35 } },
            }}
          />
        )}
        {latest && (
          <Typography sx={{ ...monoSx, fontSize: '0.75rem', color: brandTokens.text.muted }}>
            {`${notifications.length} ${notifications.length === 1 ? 'signal' : 'signals'}, last ${formatClockTime(latest.timestamp)}`}
          </Typography>
        )}
        {notifications.length > 0 && (
          <Button
            size="small"
            variant="outlined"
            onClick={handleClear}
            onKeyDown={(event) => {
              if (isConfirmingClear && event.key === 'Escape') {
                event.preventDefault();
                cancelConfirm();
              }
            }}
            aria-label={isConfirmingClear ? 'Confirm clear all signals' : 'Clear all signals'}
            sx={{
              ml: 'auto',
              minHeight: 32,
              px: 1.5,
              fontSize: '0.6875rem',
              borderColor: isConfirmingClear ? brandTokens.colors.giltEdge : brandTokens.borders.strong,
              color: isConfirmingClear ? brandTokens.colors.giltEdge : brandTokens.text.secondary,
            }}
          >
            {isConfirmingClear ? 'Confirm clear' : 'Clear'}
          </Button>
        )}
      </Box>

      {notifications.length > 0 ? (
        <Box component="ol" role="log" aria-live="polite" sx={{ m: 0, p: 0, listStyle: 'none' }}>
          {notifications.map((notification, index) => {
            const color = getNotificationColor(notification.notificationType);
            const time = formatClockTime(notification.timestamp);
            return (
              <Box
                component="li"
                key={notification.id}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: 'auto 1fr auto', sm: '76px 96px minmax(0, 1fr) auto' },
                  alignItems: 'center',
                  columnGap: 1.5,
                  py: 0.75,
                  borderBottom: index < notifications.length - 1 ? `1px solid ${brandTokens.borders.subtle}` : 'none',
                  ...monoSx,
                  fontSize: '0.8125rem',
                }}
              >
                <Box component="time" dateTime={notification.timestamp} sx={{ color: brandTokens.text.muted }}>
                  {time}
                </Box>
                <Box component="span" sx={{ color }}>
                  {notification.notificationType}
                </Box>
                <Box
                  component="span"
                  sx={{
                    gridColumn: { xs: '1 / 3', sm: 'auto' },
                    gridRow: { xs: 2, sm: 'auto' },
                    color: brandTokens.text.primary,
                    fontFamily: brandTokens.fonts.body,
                    fontSize: '0.875rem',
                    overflowWrap: 'anywhere',
                  }}
                >
                  {notification.message}
                </Box>
                <IconButton
                  size="small"
                  onClick={() => onDismiss(notification.id)}
                  aria-label={`Dismiss ${notification.notificationType} signal from ${time}`}
                  sx={{
                    gridColumn: { xs: 3, sm: 'auto' },
                    gridRow: { xs: '1 / 3', sm: 'auto' },
                    color: brandTokens.text.muted,
                    '&:hover': { color: brandTokens.text.primary, bgcolor: alpha(brandTokens.text.primary, 0.06) },
                  }}
                >
                  <X size={14} aria-hidden="true" />
                </IconButton>
              </Box>
            );
          })}
        </Box>
      ) : (
        <Typography sx={{ ...monoSx, fontSize: '0.8125rem', color: brandTokens.text.secondary }}>
          {EMPTY_FEED_TEXT[socketState](socketUrl)}
        </Typography>
      )}
    </Paper>
  );
};

export default SignalFeed;
