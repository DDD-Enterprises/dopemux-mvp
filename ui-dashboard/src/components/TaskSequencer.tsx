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
  LinearProgress,
  Divider
} from '@mui/material';
import {
  CheckCircle,
  Circle,
  PlayArrow,
  Pause,
  SkipNext,
  Timer
} from 'lucide-react';

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
      energyRequired: 'high'
    },
    {
      id: '2',
      title: 'Create UI dashboard components',
      complexity: 0.6,
      estimatedMinutes: 90,
      status: 'pending',
      energyRequired: 'medium'
    },
    {
      id: '3',
      title: 'Write unit tests',
      complexity: 0.4,
      estimatedMinutes: 45,
      status: 'pending',
      energyRequired: 'low'
    }
  ]);

  const [currentTaskId, setCurrentTaskId] = useState<string | null>('1');
  const [taskTimer, setTaskTimer] = useState<number>(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setTaskTimer(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  // Reset timer when switching tasks
  useEffect(() => {
    setTaskTimer(0);
    setIsTimerRunning(false);
  }, [currentTaskId]);

  const getOptimizedSequence = (): Task[] => {
    // Sort tasks based on cognitive state
    const sortedTasks = [...tasks].filter(task => task.status !== 'completed');

    if (cognitiveState.status === 'critical') {
      // Only show simple tasks
      return sortedTasks.filter(task => task.complexity <= 0.5);
    } else if (cognitiveState.status === 'high') {
      // Prefer medium complexity
      return sortedTasks.sort((a, b) => Math.abs(a.complexity - 0.6) - Math.abs(b.complexity - 0.6));
    } else {
      // Full sequence for optimal/low
      return sortedTasks.sort((a, b) => a.complexity - b.complexity);
    }
  };

  const startTask = (taskId: string) => {
    setTasks(prev => prev.map(task =>
      task.id === taskId ? { ...task, status: 'in_progress' as const } : task
    ));
    setCurrentTaskId(taskId);
  };

  const completeTask = (taskId: string) => {
    setTasks(prev => prev.map(task =>
      task.id === taskId ? { ...task, status: 'completed' as const } : task
    ));

    // Move to next task
    const optimizedTasks = getOptimizedSequence();
    const currentIndex = optimizedTasks.findIndex(task => task.id === taskId);
    if (currentIndex < optimizedTasks.length - 1) {
      setCurrentTaskId(optimizedTasks[currentIndex + 1].id);
    }
  };

  const skipTask = (taskId: string) => {
    const optimizedTasks = getOptimizedSequence();
    const currentIndex = optimizedTasks.findIndex(task => task.id === taskId);
    if (currentIndex < optimizedTasks.length - 1) {
      setCurrentTaskId(optimizedTasks[currentIndex + 1].id);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const optimizedTasks = getOptimizedSequence();
  const currentTask = tasks.find(task => task.id === currentTaskId);

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Timer size={24} style={{ marginRight: 8 }} />
        <Typography variant="h6">Task Sequencer</Typography>
      </Box>

      {/* Current Task Timer */}
      {currentTask && (
        <Box sx={{ mb: 3, p: 2, bgcolor: 'rgba(0, 188, 212, 0.1)', borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Current: {currentTask.title}
          </Typography>
          <Typography variant="h5" sx={{ mb: 1 }}>
            {formatTime(taskTimer)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={isTimerRunning ? <Pause /> : <PlayArrow />}
              onClick={() => setIsTimerRunning(!isTimerRunning)}
            >
              {isTimerRunning ? 'Pause' : 'Start'}
            </Button>
            <Button
              size="small"
              variant="outlined"
              startIcon={<CheckCircle />}
              onClick={() => completeTask(currentTask.id)}
            >
              Complete
            </Button>
            <Button
              size="small"
              variant="text"
              startIcon={<SkipNext />}
              onClick={() => skipTask(currentTask.id)}
            >
              Skip
            </Button>
          </Box>
        </Box>
      )}

      {/* Task Queue */}
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Optimized Sequence ({optimizedTasks.length} tasks)
      </Typography>

      <List sx={{ maxHeight: 300, overflow: 'auto' }}>
        {optimizedTasks.map((task, index) => {
          const isCurrent = task.id === currentTaskId;
          const isCompleted = task.status === 'completed';

          return (
            <React.Fragment key={task.id}>
              <ListItem
                sx={{
                  bgcolor: isCurrent ? 'rgba(0, 188, 212, 0.1)' : 'transparent',
                  borderRadius: 1,
                  mb: 0.5
                }}
              >
                <ListItemIcon>
                  {isCompleted ? (
                    <CheckCircle color="#4caf50" size={20} />
                  ) : isCurrent ? (
                    <PlayArrow color="#00bcd4" size={20} />
                  ) : (
                    <Circle size={20} />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {task.title}
                      </Typography>
                      <Chip
                        size="small"
                        label={`${(task.complexity * 100).toFixed(0)}%`}
                        sx={{
                          bgcolor: task.complexity > 0.7 ? '#f44336' :
                                   task.complexity > 0.5 ? '#ff9800' : '#4caf50',
                          color: 'white'
                        }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption">
                        {task.estimatedMinutes} min • {task.energyRequired} energy
                      </Typography>
                      <Typography variant="caption">
                        #{index + 1}
                      </Typography>
                    </Box>
                  }
                />

                {!isCompleted && !isCurrent && (
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => startTask(task.id)}
                  >
                    Start
                  </Button>
                )}
              </ListItem>

              {index < optimizedTasks.length - 1 && (
                <Divider sx={{ my: 0.5 }} />
              )}
            </React.Fragment>
          );
        })}
      </List>

      {/* Cognitive State Influence */}
      <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 1 }}>
        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
          Sequence optimized for: {cognitiveState.status.toUpperCase()} cognitive state
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
          Tasks ordered to maintain flow and prevent cognitive overload
        </Typography>
      </Box>
    </Paper>
  );
};

export default TaskSequencer;