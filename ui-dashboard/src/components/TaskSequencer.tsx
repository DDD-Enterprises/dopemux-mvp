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
    const remainingTasks = optimizedTasks.filter((task) => task.id !== taskId);
    setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status: 'completed' } : task)));
    setCurrentTaskId(remainingTasks.length > 0 ? remainingTasks[0].id : null);

    if (remainingTasks.length === 0) {
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
    const incompleteTasks = tasks.filter(t => t.status !== 'completed');
    const otherTasksTotal = incompleteTasks
      .filter(t => t.id !== currentTaskId)
      .reduce((acc, t) => acc + t.estimatedMinutes, 0);

    const currentTaskEstimate = currentTask?.estimatedMinutes || 0;
    const elapsedMinutes = taskTimer / 60;

    return Math.ceil(otherTasksTotal + Math.max(0, currentTaskEstimate - elapsedMinutes));
  }, [tasks, currentTaskId, currentTask, taskTimer]);

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
            totalRemainingMinutes === 0
              ? 'Task sequence complete'
              : getDurationAriaLabel(totalRemainingMinutes)
          }
          arrow
        >
          <Box
            role="status"
            aria-label={
              totalRemainingMinutes === 0
                ? 'Task sequence complete'
                : getDurationAriaLabel(totalRemainingMinutes)
            }
            tabIndex={0}
            sx={{
              ml: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              color: totalRemainingMinutes === 0 ? brandTokens.colors.serumMint : brandTokens.colors.saintGold,
              cursor: 'help',
              transition: 'color 0.3s ease',
              '&:focus-visible': {
                outline: 'none',
                borderRadius: 1,
                boxShadow: `0 0 0 2px ${totalRemainingMinutes === 0 ? brandTokens.colors.serumMint : brandTokens.colors.saintGold}`,
              },
            }}
          >
            {totalRemainingMinutes === 0 ? (
              <CheckCircle size={16} aria-hidden="true" />
            ) : (
              <Clock size={16} aria-hidden="true" />
            )}
            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
              {totalRemainingMinutes === 0 ? 'DONE' : `${totalRemainingMinutes}m`}
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
          <LinearProgress
            variant="determinate"
            value={Math.min(100, (taskTimer / (currentTask.estimatedMinutes * 60)) * 100)}
            sx={{
              mb: 2.5,
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
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={isTimerRunning ? 'Pause Ritual' : 'Start Ritual'} arrow>
              <Button
                size="small"
                variant="contained"
                startIcon={isTimerRunning ? <Pause /> : <Play />}
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
                startIcon={<CheckCircle />}
                onClick={() => completeTask(currentTask.id)}
                aria-label={`Complete task: ${currentTask.title}`}
              >
                Complete
              </Button>
            </Tooltip>
            <Tooltip title="Skip for Now" arrow>
              <Button
                size="small"
                variant="text"
                startIcon={<SkipForward />}
                onClick={() => skipTask(currentTask.id)}
                sx={{ color: brandTokens.colors.gremlinPink }}
                aria-label={`Skip task: ${currentTask.title}`}
              >
                Skip
              </Button>
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
          <CheckCircle size={32} color={brandTokens.colors.serumMint} style={{ marginBottom: 8 }} />
          <Typography variant="h6" sx={{ color: brandTokens.colors.serumMint, mb: 1 }}>
            Ritual Complete
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            All muzzled. Your backlog is silent... for now.
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<RotateCcw size={16} />}
            onClick={resetTasks}
            sx={{
              borderColor: brandTokens.colors.serumMint,
              color: brandTokens.colors.serumMint,
              '&:hover': {
                borderColor: brandTokens.colors.serumMint,
                background: alpha(brandTokens.colors.serumMint, 0.1),
              },
            }}
          >
            Reset Ritual
          </Button>
        </Box>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="subtitle2">
          Optimized Sequence ({optimizedTasks.length} tasks)
        </Typography>
        <Tooltip title={getDurationAriaLabel(totalRemainingMinutes)} arrow>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              ml: 'auto',
              color: brandTokens.colors.ritualCyan,
              cursor: 'help',
              '&:focus-visible': {
                outline: 'none',
                borderRadius: 1,
                boxShadow: `0 0 0 2px ${brandTokens.colors.ritualCyan}`,
              }
            }}
            tabIndex={0}
            role="status"
            aria-label={getDurationAriaLabel(totalRemainingMinutes)}
          >
            <Clock size={14} aria-hidden="true" />
            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
              {totalRemainingMinutes}m
            </Typography>
          </Box>
        </Tooltip>
        <Tooltip title="Consent → Calibration → Chaos → Care" arrow>
          <Box component="span" tabIndex={0} sx={{ display: 'flex', alignItems: 'center' }}>
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
                  bgcolor: isCurrent ? alpha(brandTokens.colors.ritualCyan, 0.08) : 'transparent',
                  borderRadius: 2,
                  border: isCurrent
                    ? `1px solid ${brandTokens.borders.cyan}`
                    : `1px solid ${brandTokens.borders.subtle}`,
                  mb: 0.5,
                }}
              >
                <ListItemIcon>
                  {isCompleted ? (
                    <CheckCircle color={brandTokens.colors.serumMint} size={20} aria-hidden="true" />
                  ) : isCurrent ? (
                    <Play color={brandTokens.colors.ritualCyan} size={20} aria-hidden="true" />
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
