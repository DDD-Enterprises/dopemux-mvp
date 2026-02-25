import React, { useState, useEffect } from 'react';
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
  alpha,
} from '@mui/material';
import {
  CheckCircle,
  Circle,
  Play,
  Pause,
  SkipForward,
  Timer,
  Flame,
  Swords,
} from 'lucide-react';
import { brandTokens } from '../theme';

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

const TaskSequencer: React.FC<TaskSequencerProps> = ({ cognitiveState }) => {
  const [tasks, setTasks] = useState<Task[]>([
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
  ]);

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

  const getOptimizedSequence = (): Task[] => {
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
  };

  const startTask = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) => (task.id === taskId ? { ...task, status: 'in_progress' } : task))
    );
    setCurrentTaskId(taskId);
  };

  const completeTask = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) => (task.id === taskId ? { ...task, status: 'completed' } : task))
    );
    const optimizedTasks = getOptimizedSequence();
    const currentIndex = optimizedTasks.findIndex((task) => task.id === taskId);
    if (currentIndex < optimizedTasks.length - 1) {
      setCurrentTaskId(optimizedTasks[currentIndex + 1].id);
    }
  };

  const skipTask = (taskId: string) => {
    const optimizedTasks = getOptimizedSequence();
    const currentIndex = optimizedTasks.findIndex((task) => task.id === taskId);
    if (currentIndex < optimizedTasks.length - 1) {
      setCurrentTaskId(optimizedTasks[currentIndex + 1].id);
    }
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

  const optimizedTasks = getOptimizedSequence();
  const currentTask = tasks.find((task) => task.id === currentTaskId);

  const complexityColor = (complexity: number) => {
    if (complexity > 0.7) return brandTokens.colors.gremlinPink;
    if (complexity > 0.5) return brandTokens.colors.giltEdge;
    return brandTokens.colors.serumMint;
  };

  return (
    <Paper sx={{ p: 3, height: '100%', borderRadius: 4 }} className="dopemux-panel">
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1.5 }}>
        <Timer size={24} aria-hidden="true" />
        <Typography variant="h6" sx={{ letterSpacing: '0.16em' }}>
          Task Sequencer
        </Typography>
        <Chip
          size="small"
          label="[LIVE]"
          className="dopemux-chip"
          sx={{ ml: 'auto', borderColor: 'rgba(125, 251, 246, 0.6)', color: brandTokens.colors.ritualCyan }}
        />
      </Box>
      <Typography className="dopemux-roast" sx={{ mb: 2 }}>
        Your backlog is feral. I muzzle it with ritual order and velvet threats.
      </Typography>

      {currentTask && (
        <Box
          sx={{
            mb: 3,
            p: 2.5,
            borderRadius: 3,
            border: '1px solid rgba(255, 207, 120, 0.5)',
            background: 'rgba(255, 207, 120, 0.08)',
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 0.5, letterSpacing: '0.08em' }}>
            Current Ritual
          </Typography>
          <Typography variant="h5" sx={{ mb: 0.5 }}>
            {currentTask.title}
          </Typography>
          <Typography
            variant="h3"
            role="timer"
            aria-label={getTimerAriaLabel(taskTimer)}
            sx={{
              fontFamily: '"Space Grotesk", sans-serif',
              mb: 1,
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
          <LinearProgress
            variant="determinate"
            value={Math.min(100, (taskTimer / (currentTask.estimatedMinutes * 60)) * 100)}
            sx={{
              mb: 2.5,
              height: 6,
              borderRadius: 3,
              bgcolor: alpha(brandTokens.colors.saintGold, 0.1),
              '& .MuiLinearProgress-bar': {
                bgcolor: brandTokens.colors.saintGold,
                borderRadius: 3,
              },
            }}
            aria-label="Current task progress"
            aria-valuetext={`${Math.round(Math.min(100, (taskTimer / (currentTask.estimatedMinutes * 60)) * 100))}% of estimated time`}
          />
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={isTimerRunning ? 'Pause Ritual' : 'Start Ritual'}>
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
            <Tooltip title="Complete and Proceed">
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
            <Tooltip title="Skip for Now">
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
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="subtitle2">
          Optimized Sequence ({optimizedTasks.length} tasks)
        </Typography>
        <Tooltip title="Consent → Calibration → Chaos → Care">
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
                sx={{
                  bgcolor: isCurrent ? 'rgba(125, 251, 246, 0.08)' : 'transparent',
                  borderRadius: 2,
                  border: isCurrent ? '1px solid rgba(125, 251, 246, 0.4)' : '1px solid rgba(255,255,255,0.05)',
                  mb: 0.5,
                }}
              >
                <ListItemIcon>
                  {isCompleted ? (
                    <CheckCircle color={brandTokens.colors.serumMint} size={20} aria-hidden="true" />
                  ) : isCurrent ? (
                    <Play color={brandTokens.colors.ritualCyan} size={20} aria-hidden="true" />
                  ) : (
                    <Circle color="rgba(255, 255, 255, 0.3)" size={18} aria-hidden="true" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {task.title}
                      </Typography>
                      <Tooltip title={`Complexity: ${Math.round(task.complexity * 100)}% - used for ritual sequencing`}>
                        <Chip
                          size="small"
                          label={`${Math.round(task.complexity * 100)}% complex`}
                          tabIndex={0}
                          sx={{
                            bgcolor: 'rgba(4,22,40,0.8)',
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
                <Divider sx={{ my: 0.5, borderColor: 'rgba(255,255,255,0.05)' }} />
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
          border: '1px dashed rgba(125, 251, 246, 0.3)',
          bgcolor: 'rgba(2,6,23,0.45)',
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
