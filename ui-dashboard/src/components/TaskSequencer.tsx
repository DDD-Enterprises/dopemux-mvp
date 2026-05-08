import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Paper,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Chip,
  Divider,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import {
  CheckCircle,
  Circle,
  Play,
  Pause,
  SkipForward,
  Timer,
  Clock,
  Flame,
  Swords,
  RotateCcw,
  AlertTriangle,
} from 'lucide-react';
import { brandTokens, statusStyles } from '../theme';

interface Task {
  id: string;
  title: string;
  complexity: number;
  estimatedMinutes: number;
  status: 'pending' | 'in_progress' | 'completed';
  energyRequired: string;
}

interface CognitiveState {
  energy: number;
  attention: number;
  load: number;
  status: 'low' | 'optimal' | 'high' | 'critical';
  recommendation: string;
}

interface TaskSequencerProps {
  cognitiveState: CognitiveState;
}

const INITIAL_TASKS: Task[] = [
  {
    id: '1',
    title: 'Implement LSTM cognitive predictor',
    complexity: 0.8,
    estimatedMinutes: 120,
    status: 'in_progress',
    energyRequired: 'high',
  },
  {
    id: '2',
    title: 'Create UI dashboard components',
    complexity: 0.6,
    estimatedMinutes: 90,
    status: 'pending',
    energyRequired: 'medium',
  },
  {
    id: '3',
    title: 'Write unit tests',
    complexity: 0.4,
    estimatedMinutes: 45,
    status: 'pending',
    energyRequired: 'low',
  },
];

const TaskSequencer: React.FC<TaskSequencerProps> = ({ cognitiveState }) => {
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
  const headerRef = useRef<HTMLHeadingElement>(null);

  const [currentTaskId, setCurrentTaskId] = useState<string | null>('1');
  const [taskTimer, setTaskTimer] = useState<number>(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [isResetConfirming, setIsResetConfirming] = useState(false);
  const resetTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setTaskTimer((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  useEffect(() => {
    setTaskTimer(0);
    setIsTimerRunning(false);
  }, [currentTaskId]);

  useEffect(() => {
    return () => {
      if (resetTimeoutRef.current) {
        clearTimeout(resetTimeoutRef.current);
      }
    };
  }, []);

  const optimizedTasks = useMemo(() => {
    const sortedTasks = [...tasks].filter((task) => task.status !== 'completed');

    if (cognitiveState.status === 'critical') {
      return sortedTasks.filter((task) => task.complexity <= 0.5);
    }
    if (cognitiveState.status === 'high') {
      return sortedTasks.sort(
        (a, b) => Math.abs(a.complexity - 0.6) - Math.abs(b.complexity - 0.6)
      );
    }
    return sortedTasks.sort((a, b) => a.complexity - b.complexity);
  }, [tasks, cognitiveState.status]);

  const startTask = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) => (task.id === taskId ? { ...task, status: 'in_progress' } : task))
    );
    setCurrentTaskId(taskId);
  };

  const completeTask = (taskId: string) => {
    setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status: 'completed' } : task)));
    const remainingTasks = tasks.filter((task) => task.id !== taskId && task.status !== 'completed');
    const nextTask = optimizedTasks.find((task) => task.id !== taskId) ?? remainingTasks[0];
    setCurrentTaskId(nextTask ? nextTask.id : null);
    if (!nextTask) {
      headerRef.current?.focus();
    }
  };

  const skipTask = (taskId: string) => {
    if (optimizedTasks.length <= 1) return;
    const currentIndex = optimizedTasks.findIndex((task) => task.id === taskId);
    const nextIndex = (currentIndex + 1) % optimizedTasks.length;
    setCurrentTaskId(optimizedTasks[nextIndex].id);
  };

  const resetTasks = () => {
    if (!isResetConfirming) {
      setIsResetConfirming(true);
      if (resetTimeoutRef.current) clearTimeout(resetTimeoutRef.current);
      resetTimeoutRef.current = setTimeout(() => {
        setIsResetConfirming(false);
        resetTimeoutRef.current = null;
      }, 3000);
      return;
    }

    if (resetTimeoutRef.current) {
      clearTimeout(resetTimeoutRef.current);
      resetTimeoutRef.current = null;
    }
    setIsResetConfirming(false);

    const freshTasks = INITIAL_TASKS.map((task) => ({ ...task }));
    setTasks(freshTasks);
    setCurrentTaskId(freshTasks[0].id);
    setTaskTimer(0);
    setIsTimerRunning(false);
    headerRef.current?.focus();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimerAriaLabel = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    const minLabel = mins === 1 ? '1 minute' : `${mins} minutes`;
    const secLabel = secs === 1 ? '1 second' : `${secs} seconds`;

    if (mins > 0) {
      return `Time elapsed: ${minLabel} and ${secLabel}`;
    }
    return `Time elapsed: ${secLabel}`;
  };

  const getDurationAriaLabel = (minutes: number): string => {
    const label = minutes === 1 ? '1 minute' : `${minutes} minutes`;
    return `Total remaining duration: ${label}`;
  };

  const currentTask = tasks.find((task) => task.id === currentTaskId);
  const statusTone = statusStyles[cognitiveState.status];

  const isOvertime = useMemo(() => {
    if (!currentTask) return false;
    return (taskTimer / 60) > currentTask.estimatedMinutes;
  }, [currentTask, taskTimer]);

  const overtimeMinutes = isOvertime
    ? Math.floor(taskTimer / 60 - currentTask!.estimatedMinutes)
    : 0;

  const complexityColor = (complexity: number) => {
    if (complexity > 0.7) return brandTokens.colors.gremlinPink;
    if (complexity > 0.5) return brandTokens.colors.giltEdge;
    return brandTokens.colors.serumMint;
  };

  const totalRemainingMinutes = useMemo(() => {
    const incompleteTasks = tasks.filter((t) => t.status !== 'completed');
    const otherTasksTotal = incompleteTasks
      .filter((t) => t.id !== currentTaskId)
      .reduce((acc, t) => acc + t.estimatedMinutes, 0);

    const currentTaskEstimate = currentTask?.estimatedMinutes || 0;
    const elapsedMinutes = taskTimer / 60;

    return otherTasksTotal + Math.max(0, currentTaskEstimate - elapsedMinutes);
  }, [tasks, currentTaskId, currentTask, taskTimer]);

  const displayRemainingMinutes = Math.ceil(totalRemainingMinutes);

  const { completedCount, totalCount, isComplete } = useMemo(() => {
    const completed = tasks.filter((t) => t.status === 'completed').length;
    const total = tasks.length;
    return {
      completedCount: completed,
      totalCount: total,
      // Real completion state: every task is marked done.
      // Distinct from displayRemainingMinutes === 0, which can fire when the
      // current task overruns its estimate but later tasks remain.
      isComplete: total > 0 && completed === total,
    };
  }, [tasks]);

  const finishTimeLabel = useMemo(() => {
    if (totalRemainingMinutes === 0) return '';
    // Use fractional minutes to ensure a stable finish time that only moves with taskTimer
    const finishDate = new Date(Date.now() + totalRemainingMinutes * 60000);
    const hh = finishDate.getHours().toString().padStart(2, '0');
    const mm = finishDate.getMinutes().toString().padStart(2, '0');
    return `Finish at ${hh}:${mm}`;
  }, [totalRemainingMinutes]);

  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        borderRadius: 4,
        background: brandTokens.gradients.focusCard,
        border: `1px solid ${statusTone.border}`,
        boxShadow: statusTone.shadow,
      }}
      className="dopemux-panel"
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1.5 }}>
        <Timer size={24} aria-hidden="true" />
        <Typography
          variant="h6"
          ref={headerRef}
          tabIndex={-1}
          sx={{ letterSpacing: '0.16em', outline: 'none' }}
        >
          Task Sequencer
        </Typography>
        <Tooltip
          title={
            isComplete
              ? 'Task sequence complete'
              : `${completedCount}/${totalCount} tasks • ${getDurationAriaLabel(displayRemainingMinutes)} (${finishTimeLabel})`
          }
          arrow
        >
          <Box
            role="status"
            aria-label={
              isComplete
                ? 'Task sequence complete'
                : `${completedCount}/${totalCount} tasks completed. ${getDurationAriaLabel(displayRemainingMinutes)}. Estimated completion: ${finishTimeLabel}`
            }
            tabIndex={0}
            sx={{
              ml: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: isComplete ? brandTokens.colors.serumMint : brandTokens.colors.saintGold,
              cursor: 'help',
              transition: 'all 0.3s ease',
              ...(isComplete && {
                animation: 'done-glow 2s infinite ease-in-out',
                '@keyframes done-glow': {
                  '0%, 100%': { transform: 'scale(1)', filter: 'drop-shadow(0 0 0px transparent)' },
                  '50%': { transform: 'scale(1.05)', filter: `drop-shadow(0 0 4px ${alpha(brandTokens.colors.serumMint, 0.4)})` },
                },
              }),
              '&:focus-visible': {
                outline: 'none',
                borderRadius: 1,
                boxShadow: `0 0 0 2px ${isComplete ? brandTokens.colors.serumMint : brandTokens.colors.saintGold}`,
              },
            }}
          >
            {isComplete ? (
              <CheckCircle size={16} aria-hidden="true" />
            ) : (
              <Clock size={16} aria-hidden="true" />
            )}
            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
              {isComplete ? 'DONE' : `${completedCount}/${totalCount} • ${displayRemainingMinutes}m`}
            </Typography>
          </Box>
        </Tooltip>
        <Tooltip title="Real-time task synchronization active" arrow>
          <Chip
            size="small"
            label="[LIVE]"
            className="dopemux-chip"
            tabIndex={0}
            sx={{
              ml: 'auto',
              borderColor: brandTokens.borders.cyan,
              color: brandTokens.colors.ritualCyan,
              bgcolor: alpha(brandTokens.colors.ritualCyan, 0.08),
            }}
            aria-label="Real-time task synchronization active"
          />
        </Tooltip>
      </Box>
      <Typography className="dopemux-roast" sx={{ mb: 2 }}>
        Your backlog is feral. I muzzle it with ritual order and velvet threats.
      </Typography>

      {currentTask ? (
        <Box
          sx={{
            mb: 3,
            p: 2.5,
            borderRadius: 3,
            border: `1px solid ${brandTokens.borders.gold}`,
            background: alpha(brandTokens.colors.saintGold, 0.08),
            boxShadow: brandTokens.shadows.goldBloom,
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 0.5, letterSpacing: '0.08em' }}>
            Current Ritual
          </Typography>
          <Typography variant="h5" sx={{ mb: 0.5 }}>
            {currentTask.title}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5 }}>
            <Typography
              variant="h3"
              role="timer"
              aria-label={getTimerAriaLabel(taskTimer)}
              sx={{
                fontFamily: '"Space Grotesk", sans-serif',
                mb: 1,
                color: isOvertime ? brandTokens.colors.gremlinPink : 'inherit',
                ...(isTimerRunning && {
                  animation: 'timer-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                  '@keyframes timer-pulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.6 },
                  },
                }),
              }}
            >
              {formatTime(taskTimer)}
            </Typography>
            {isOvertime && (
              <Typography
                variant="caption"
                sx={{
                  color: brandTokens.colors.gremlinPink,
                  fontWeight: 'bold',
                  letterSpacing: '0.1em',
                  bgcolor: alpha(brandTokens.colors.gremlinPink, 0.1),
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  border: `1px solid ${alpha(brandTokens.colors.gremlinPink, 0.3)}`,
                }}
              >
                OVERTIME +{overtimeMinutes}M
              </Typography>
            )}
          </Box>
          <Tooltip title="Current task progress based on estimate" arrow>
            <Box
              tabIndex={0}
              sx={{
                mb: 2.5,
                outline: 'none',
                cursor: 'help',
                '&:focus-visible': {
                  borderRadius: 1,
                  boxShadow: `0 0 0 2px ${brandTokens.colors.ritualCyan}`,
                },
              }}
            >
              <LinearProgress
                variant="determinate"
                value={Math.min(100, (taskTimer / (currentTask.estimatedMinutes * 60)) * 100)}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  bgcolor: alpha(isOvertime ? brandTokens.colors.gremlinPink : brandTokens.colors.saintGold, 0.1),
                  '& .MuiLinearProgress-bar': {
                    bgcolor: isOvertime ? brandTokens.colors.gremlinPink : brandTokens.colors.saintGold,
                    borderRadius: 3,
                    boxShadow: isOvertime
                      ? `0 0 12px ${alpha(brandTokens.colors.gremlinPink, 0.6)}`
                      : brandTokens.shadows.goldBloom,
                  },
                }}
                aria-label="Current task progress"
                aria-valuetext={
                  isOvertime
                    ? `Overtime: ${Math.floor(taskTimer / 60 - currentTask.estimatedMinutes)} ${
                        Math.floor(taskTimer / 60 - currentTask.estimatedMinutes) === 1 ? 'minute' : 'minutes'
                      } past estimate`
                    : `${Math.round(Math.min(100, (taskTimer / (currentTask.estimatedMinutes * 60)) * 100))}% of estimated time`
                }
              />
            </Box>
          </Tooltip>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={isTimerRunning ? 'Pause Ritual' : 'Start Ritual'} arrow>
              <Button
                size="small"
                variant="contained"
                startIcon={isTimerRunning ? <Pause aria-hidden="true" /> : <Play aria-hidden="true" />}
                onClick={() => setIsTimerRunning(!isTimerRunning)}
                aria-label={isTimerRunning ? `Pause task: ${currentTask.title}` : `Start task: ${currentTask.title}`}
              >
                {isTimerRunning ? 'Pause' : 'Start'}
              </Button>
            </Tooltip>
            <Tooltip title="Complete and Proceed" arrow>
              <Button
                size="small"
                variant="outlined"
                startIcon={<CheckCircle aria-hidden="true" />}
                onClick={() => completeTask(currentTask.id)}
                aria-label={`Complete task: ${currentTask.title}`}
              >
                Complete
              </Button>
            </Tooltip>
            <Tooltip title={optimizedTasks.length <= 1 ? 'No other tasks to skip to' : 'Skip for Now'} arrow>
              <Box
                component="span"
                tabIndex={optimizedTasks.length <= 1 ? 0 : -1}
                aria-disabled={optimizedTasks.length <= 1 ? 'true' : undefined}
                sx={{
                  display: 'inline-flex',
                  borderRadius: 1,
                  outline: 'none',
                  '&:focus-visible': {
                    boxShadow: `0 0 0 2px ${brandTokens.colors.gremlinPink}`,
                  },
                }}
              >
                <Button
                  size="small"
                  variant="text"
                  startIcon={<SkipForward aria-hidden="true" />}
                  onClick={() => skipTask(currentTask.id)}
                  sx={{ color: brandTokens.colors.gremlinPink }}
                  aria-label={`Skip task: ${currentTask.title}`}
                  disabled={optimizedTasks.length <= 1}
                >
                  Skip
                </Button>
              </Box>
            </Tooltip>
          </Box>
        </Box>
      ) : (
        <Box
          role="status"
          aria-label="Ritual Complete: All tasks finished"
          sx={{
            mb: 3,
            p: 2.5,
            borderRadius: 3,
            textAlign: 'center',
            border: `1px solid ${brandTokens.borders.mint}`,
            background: alpha(brandTokens.colors.serumMint, 0.05),
          }}
        >
          <CheckCircle size={32} color={brandTokens.colors.serumMint} style={{ marginBottom: 8 }} aria-hidden="true" />
          <Typography variant="h6" sx={{ color: brandTokens.colors.serumMint, mb: 1 }}>
            Ritual Complete
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            All muzzled. Your backlog is silent... for now.
          </Typography>
          <Tooltip title={isResetConfirming ? 'Confirm to clear all progress' : 'Restart the task sequence'} arrow>
            <Button
              variant="outlined"
              size="small"
              startIcon={
                isResetConfirming ? (
                  <AlertTriangle size={16} aria-hidden="true" />
                ) : (
                  <RotateCcw size={16} aria-hidden="true" />
                )
              }
              onClick={resetTasks}
              sx={{
                borderColor: isResetConfirming ? brandTokens.colors.saintGold : brandTokens.colors.serumMint,
                color: isResetConfirming ? brandTokens.colors.saintGold : brandTokens.colors.serumMint,
                transition: [
                  'color 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  'border-color 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  'background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  'box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                ].join(', '),
                ...(isResetConfirming && {
                  animation: 'reset-pulse 1.5s infinite',
                  '@keyframes reset-pulse': {
                    '0%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(1.03)', boxShadow: `0 0 12px ${alpha(brandTokens.colors.saintGold, 0.3)}` },
                    '100%': { transform: 'scale(1)' },
                  },
                }),
                '&:hover': {
                  borderColor: isResetConfirming ? brandTokens.colors.saintGold : brandTokens.colors.serumMint,
                  background: alpha(
                    isResetConfirming ? brandTokens.colors.saintGold : brandTokens.colors.serumMint,
                    0.1
                  ),
                },
              }}
            >
              {isResetConfirming ? 'Confirm Reset?' : 'Reset Ritual'}
            </Button>
          </Tooltip>
        </Box>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="subtitle2">
          Optimized Sequence ({optimizedTasks.length} tasks)
        </Typography>
        <Tooltip
          title={
            isComplete
              ? 'Task sequence complete'
              : `${completedCount}/${totalCount} tasks • ${getDurationAriaLabel(displayRemainingMinutes)} (${finishTimeLabel})`
          }
          arrow
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              ml: 'auto',
              color: isComplete ? brandTokens.colors.serumMint : brandTokens.colors.ritualCyan,
              cursor: 'help',
              transition: 'all 0.3s ease',
              ...(isComplete && {
                animation: 'done-glow 2s infinite ease-in-out',
              }),
              '&:focus-visible': {
                outline: 'none',
                borderRadius: 1,
                boxShadow: `0 0 0 2px ${isComplete ? brandTokens.colors.serumMint : brandTokens.colors.ritualCyan}`,
              }
            }}
            tabIndex={0}
            role="status"
            aria-label={
              isComplete
                ? 'Task sequence complete'
                : `${completedCount}/${totalCount} tasks completed. ${getDurationAriaLabel(displayRemainingMinutes)}. Estimated completion: ${finishTimeLabel}`
            }
          >
            {isComplete ? (
              <CheckCircle size={14} aria-hidden="true" />
            ) : (
              <Clock size={14} aria-hidden="true" />
            )}
            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
              {isComplete ? 'DONE' : `${completedCount}/${totalCount} • ${displayRemainingMinutes}m`}
            </Typography>
          </Box>
        </Tooltip>
        <Tooltip title="Ritual phases: Consent, Calibration, Chaos, and Care" arrow>
          <Box
            component="span"
            tabIndex={0}
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'help',
              outline: 'none',
              borderRadius: 1,
              '&:focus-visible': {
                boxShadow: `0 0 0 2px ${brandTokens.colors.gremlinPink}`,
              },
            }}
            aria-label="Ritual phases: Consent, Calibration, Chaos, and Care"
          >
            <Flame size={16} color={brandTokens.colors.gremlinPink} aria-hidden="true" />
          </Box>
        </Tooltip>
      </Box>

      <List sx={{ maxHeight: 300, overflow: 'auto' }}>
        {optimizedTasks.map((task, index) => {
          const isCurrent = task.id === currentTaskId;
          const isCompleted = task.status === 'completed';

          return (
            <React.Fragment key={task.id}>
              <ListItem
                alignItems="flex-start"
                aria-current={isCurrent ? 'step' : undefined}
                sx={{
                  position: 'relative',
                  bgcolor: isCurrent ? alpha(brandTokens.colors.ritualCyan, 0.08) : 'transparent',
                  borderRadius: 2,
                  border: isCurrent
                    ? `1px solid ${brandTokens.borders.cyan}`
                    : `1px solid ${brandTokens.borders.subtle}`,
                  mb: 0.5,
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover, &:focus-within': {
                    bgcolor: isCurrent
                      ? alpha(brandTokens.colors.ritualCyan, 0.12)
                      : alpha(brandTokens.colors.ritualCyan, 0.04),
                    transform: 'translateY(-2px)',
                    boxShadow: `0 4px 12px ${alpha(brandTokens.colors.inkBlack, 0.4)}`,
                    borderColor: alpha(brandTokens.colors.ritualCyan, 0.4),
                    // Lift above the next sibling so the drop shadow isn't clipped.
                    zIndex: 1,
                  },
                }}
              >
                <ListItemIcon>
                  {isCompleted ? (
                    <CheckCircle color={brandTokens.colors.serumMint} size={20} aria-hidden="true" />
                  ) : isCurrent ? (
                    <Play
                      color={brandTokens.colors.ritualCyan}
                      size={20}
                      aria-hidden="true"
                      style={{
                        animation: isTimerRunning ? 'timer-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none'
                      }}
                    />
                  ) : (
                    <Circle color={alpha(brandTokens.text.primary, 0.3)} size={18} aria-hidden="true" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {task.title}
                      </Typography>
                      <Tooltip title={`Complexity: ${Math.round(task.complexity * 100)}% - used for ritual sequencing`} arrow>
                        <Chip
                          size="small"
                          label={`${Math.round(task.complexity * 100)}% complex`}
                          tabIndex={0}
                          sx={{
                            bgcolor: brandTokens.surfaces.chip,
                            color: complexityColor(task.complexity),
                            border: `1px solid ${complexityColor(task.complexity)}`,
                          }}
                        />
                      </Tooltip>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption">
                        {task.estimatedMinutes} min • {task.energyRequired} energy
                      </Typography>
                      <Typography variant="caption">#{index + 1}</Typography>
                    </Box>
                  }
                />
                {!isCompleted && !isCurrent && (
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<Play aria-hidden="true" />}
                    onClick={() => startTask(task.id)}
                    aria-label={`Start task: ${task.title}`}
                  >
                    Start
                  </Button>
                )}
              </ListItem>
              {index < optimizedTasks.length - 1 && (
                <Divider sx={{ my: 0.5, borderColor: brandTokens.borders.subtle }} />
              )}
            </React.Fragment>
          );
        })}
      </List>

      <Box
        sx={{
          mt: 2,
          p: 2,
          borderRadius: 2,
          border: `1px dashed ${brandTokens.borders.cyan}`,
          bgcolor: brandTokens.surfaces.panel,
        }}
      >
        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
          Sequencer calibrated for {cognitiveState.status.toUpperCase()} load.
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
          <Swords size={12} style={{ marginRight: 6 }} aria-hidden="true" />
          I reorder your chaos so you can stay feral on purpose.
        </Typography>
        <Typography className="dopemux-aftercare" sx={{ mt: 0.5 }}>
          [AFTERCARE] Logged. Hydrate. Ask for mercy with details.
        </Typography>
      </Box>
    </Paper>
  );
};

export default TaskSequencer;
