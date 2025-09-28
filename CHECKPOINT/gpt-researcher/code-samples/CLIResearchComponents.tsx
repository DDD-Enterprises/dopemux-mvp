/**
 * React Ink CLI Components for ADHD-Optimized Research in Dopemux
 *
 * These components work in terminal environments using React Ink
 */

import React, { useState, useEffect } from 'react';
import { Box, Text, useInput, useApp, Newline } from 'ink';
import { ResearchChunk, ProgressState, AttentionState } from './adhd-research-manager';

// Main Research Progress CLI Component
export const CLIResearchProgress: React.FC<{
  progress: ProgressState;
  attentionState: AttentionState;
  onBreakRequested?: () => void;
  onContinue?: () => void;
}> = ({ progress, attentionState, onBreakRequested, onContinue }) => {
  const [showBreakPrompt, setShowBreakPrompt] = useState(false);

  // Handle keyboard input
  useInput((input, key) => {
    if (input === 'b' && onBreakRequested) {
      setShowBreakPrompt(true);
    }
    if (input === 'c' && onContinue) {
      onContinue();
    }
    if (key.escape) {
      setShowBreakPrompt(false);
    }
  });

  if (showBreakPrompt) {
    return (
      <CLIBreakPrompt
        onBreakChoice={(duration) => {
          setShowBreakPrompt(false);
          onBreakRequested?.();
        }}
        onContinue={() => {
          setShowBreakPrompt(false);
          onContinue?.();
        }}
        onCancel={() => setShowBreakPrompt(false)}
      />
    );
  }

  return (
    <Box flexDirection="column" padding={1}>
      <CLIProgressBar progress={progress} />
      <Newline />
      <CLICurrentActivity progress={progress} />
      <Newline />
      <CLITimeAwareness progress={progress} />
      <Newline />
      <CLIAttentionState state={attentionState} />
      <Newline />
      <CLIKeyboardHints />
    </Box>
  );
};

// Terminal Progress Bar with ADHD-friendly visualization
const CLIProgressBar: React.FC<{ progress: ProgressState }> = ({ progress }) => {
  const totalBlocks = 8;
  const completedBlocks = Math.floor((progress.completedChunks.length / progress.totalChunks) * totalBlocks);
  const currentBlock = progress.currentChunk > 0 ? 1 : 0;

  // Create visual progress
  const filled = '█'.repeat(completedBlocks);
  const current = currentBlock ? '▓' : '';
  const empty = '░'.repeat(Math.max(0, totalBlocks - completedBlocks - currentBlock));
  const progressBar = `[${filled}${current}${empty}]`;

  const percentage = Math.round((progress.completedChunks.length / progress.totalChunks) * 100);

  return (
    <Box flexDirection="column">
      <Box>
        <Text color="cyan" bold>Research Progress </Text>
        <Text color="white">{progressBar} </Text>
        <Text color="green">{percentage}%</Text>
      </Box>
      <Box marginTop={1}>
        <Text color="blue">
          📊 {progress.completedChunks.length}/{progress.totalChunks} chunks complete
        </Text>
        {progress.completedChunks.length > 0 && (
          <Text color="green"> ✅</Text>
        )}
      </Box>
    </Box>
  );
};

// Current Activity Display for CLI
const CLICurrentActivity: React.FC<{ progress: ProgressState }> = ({ progress }) => {
  const [dots, setDots] = useState('');

  // Animate activity dots
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <Box flexDirection="column">
      <Box>
        <Text color="yellow">🔍 Current Activity:</Text>
      </Box>
      <Box marginLeft={3}>
        <Text color="white">
          {progress.currentActivity}
          <Text color="gray">{dots}</Text>
        </Text>
      </Box>
    </Box>
  );
};

// Time Awareness for CLI
const CLITimeAwareness: React.FC<{ progress: ProgressState }> = ({ progress }) => {
  const formatTime = (minutes: number): string => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const timeSpentColor = progress.timeSpent > 30 ? 'yellow' : 'green';
  const isLongSession = progress.timeSpent > 45;

  return (
    <Box flexDirection="column">
      <Box>
        <Text color="cyan">⏱️  Time Spent: </Text>
        <Text color={timeSpentColor}>{formatTime(progress.timeSpent)}</Text>

        <Text color="cyan">  🎯 Remaining: </Text>
        <Text color="green">
          {progress.estimatedTimeRemaining > 0
            ? `~${formatTime(progress.estimatedTimeRemaining)}`
            : 'Almost done!'
          }
        </Text>
      </Box>

      {isLongSession && (
        <Box marginTop={1}>
          <Text color="yellow" bold>
            ⚠️  Long session detected - consider a break soon
          </Text>
        </Box>
      )}
    </Box>
  );
};

// Attention State Indicator for CLI
const CLIAttentionState: React.FC<{ state: AttentionState }> = ({ state }) => {
  const getStateDisplay = () => {
    switch (state.type) {
      case 'hyperfocus':
        return {
          icon: '🔥',
          color: 'red' as const,
          message: 'HYPERFOCUS MODE',
          description: 'Deep focus detected - set timer to avoid burnout'
        };
      case 'scattered':
        return {
          icon: '🌀',
          color: 'yellow' as const,
          message: 'SCATTERED ATTENTION',
          description: 'Try smaller chunks or take a movement break'
        };
      case 'fatigued':
        return {
          icon: '😴',
          color: 'red' as const,
          message: 'ATTENTION FATIGUE',
          description: 'Break recommended - your brain needs rest'
        };
      case 'optimal':
        return {
          icon: '✨',
          color: 'green' as const,
          message: 'OPTIMAL FOCUS',
          description: 'Perfect attention state for productive work'
        };
    }
  };

  const display = getStateDisplay();

  // Energy bar for CLI
  const energyBlocks = Math.round((state.energy / 100) * 10);
  const energyBar = '█'.repeat(energyBlocks) + '░'.repeat(10 - energyBlocks);
  const energyColor = state.energy > 60 ? 'green' : state.energy > 30 ? 'yellow' : 'red';

  return (
    <Box flexDirection="column">
      <Box>
        <Text color={display.color}>{display.icon} {display.message}</Text>
      </Box>
      <Box marginLeft={3}>
        <Text color="gray">{display.description}</Text>
      </Box>
      <Box marginTop={1} marginLeft={3}>
        <Text color="cyan">Energy: </Text>
        <Text color={energyColor}>[{energyBar}] {state.energy}%</Text>
      </Box>
    </Box>
  );
};

// Break Prompt for CLI
const CLIBreakPrompt: React.FC<{
  onBreakChoice: (duration: number) => void;
  onContinue: () => void;
  onCancel: () => void;
}> = ({ onBreakChoice, onContinue, onCancel }) => {
  const [selectedOption, setSelectedOption] = useState(0);

  const options = [
    { key: '1', duration: 5, label: '5-minute micro-break', icon: '☕' },
    { key: '2', duration: 15, label: '15-minute break', icon: '🚶' },
    { key: '3', duration: 30, label: '30-minute break', icon: '🍃' },
    { key: 'c', duration: 0, label: 'Continue working', icon: '💪' }
  ];

  useInput((input, key) => {
    if (key.upArrow && selectedOption > 0) {
      setSelectedOption(selectedOption - 1);
    }
    if (key.downArrow && selectedOption < options.length - 1) {
      setSelectedOption(selectedOption + 1);
    }
    if (key.return) {
      const option = options[selectedOption];
      if (option.duration === 0) {
        onContinue();
      } else {
        onBreakChoice(option.duration);
      }
    }
    if (key.escape) {
      onCancel();
    }

    // Direct key selection
    const option = options.find(opt => opt.key === input);
    if (option) {
      if (option.duration === 0) {
        onContinue();
      } else {
        onBreakChoice(option.duration);
      }
    }
  });

  return (
    <Box flexDirection="column" padding={1} borderStyle="round" borderColor="yellow">
      <Box marginBottom={1}>
        <Text color="green" bold>🎯 Great Progress! Time for a break?</Text>
      </Box>

      {options.map((option, index) => (
        <Box key={option.key} marginLeft={1}>
          <Text color={selectedOption === index ? 'cyan' : 'white'}>
            {selectedOption === index ? '→ ' : '  '}
            {option.icon} [{option.key}] {option.label}
          </Text>
        </Box>
      ))}

      <Box marginTop={1}>
        <Text color="gray">
          Use ↑↓ arrows or number keys to select, Enter to confirm, Esc to cancel
        </Text>
      </Box>
    </Box>
  );
};

// Research Chunk Display for CLI
export const CLIChunkDisplay: React.FC<{
  chunks: ResearchChunk[];
  currentChunkIndex: number;
}> = ({ chunks, currentChunkIndex }) => {
  return (
    <Box flexDirection="column" padding={1}>
      <Text color="cyan" bold>Research Chunks:</Text>
      <Newline />

      {chunks.map((chunk, index) => (
        <CLIChunkCard
          key={chunk.id}
          chunk={chunk}
          isActive={index === currentChunkIndex}
          isCurrent={index === currentChunkIndex}
        />
      ))}
    </Box>
  );
};

// Individual Chunk Card for CLI
const CLIChunkCard: React.FC<{
  chunk: ResearchChunk;
  isActive: boolean;
  isCurrent: boolean;
}> = ({ chunk, isActive, isCurrent }) => {
  const getStatusIcon = () => {
    switch (chunk.status) {
      case 'completed': return '✅';
      case 'active': return '🔄';
      case 'paused': return '⏸️';
      default: return '⏳';
    }
  };

  const getStatusColor = () => {
    switch (chunk.status) {
      case 'completed': return 'green' as const;
      case 'active': return 'blue' as const;
      case 'paused': return 'yellow' as const;
      default: return 'gray' as const;
    }
  };

  // Progress bar for active chunk
  const progressBlocks = Math.round((chunk.progress / 100) * 6);
  const progressBar = '█'.repeat(progressBlocks) + '░'.repeat(6 - progressBlocks);

  return (
    <Box
      flexDirection="column"
      marginBottom={1}
      borderStyle={isCurrent ? 'round' : undefined}
      borderColor={isCurrent ? 'blue' : undefined}
      padding={isCurrent ? 1 : 0}
    >
      <Box>
        <Text color={getStatusColor()}>
          {getStatusIcon()} {chunk.id}
        </Text>
        <Text color="gray"> ({chunk.estimatedDuration}m)</Text>
      </Box>

      <Box marginLeft={3}>
        <Text color="white">{chunk.query}</Text>
      </Box>

      {chunk.status === 'active' && (
        <Box marginLeft={3} marginTop={1}>
          <Text color="blue">[{progressBar}] {chunk.progress}%</Text>
        </Box>
      )}

      {chunk.breakAfter && (
        <Box marginLeft={3}>
          <Text color="yellow">☕ Break after this chunk</Text>
        </Box>
      )}
    </Box>
  );
};

// Session Resume for CLI
export const CLISessionResume: React.FC<{
  sessionSummary: string;
  timeAway: number;
  onResume: () => void;
  onStartFresh: () => void;
}> = ({ sessionSummary, timeAway, onResume, onStartFresh }) => {
  const [selectedOption, setSelectedOption] = useState(0);

  const formatTimeAway = (minutes: number): string => {
    if (minutes < 60) return `${Math.round(minutes)} minutes`;
    if (minutes < 1440) return `${Math.round(minutes / 60)} hours`;
    return `${Math.round(minutes / 1440)} days`;
  };

  useInput((input, key) => {
    if (key.upArrow || key.leftArrow) {
      setSelectedOption(0);
    }
    if (key.downArrow || key.rightArrow) {
      setSelectedOption(1);
    }
    if (key.return) {
      if (selectedOption === 0) {
        onResume();
      } else {
        onStartFresh();
      }
    }
    if (input === 'r') onResume();
    if (input === 'f') onStartFresh();
  });

  return (
    <Box flexDirection="column" padding={2} borderStyle="double" borderColor="green">
      <Text color="green" bold>👋 Welcome Back!</Text>
      <Text color="gray">You've been away for {formatTimeAway(timeAway)}</Text>
      <Newline />

      <Text color="cyan" bold>Where you left off:</Text>
      <Box marginLeft={2} marginTop={1}>
        <Text color="white">{sessionSummary}</Text>
      </Box>
      <Newline />

      <Text color="yellow" bold>What would you like to do?</Text>

      <Box marginTop={1}>
        <Text color={selectedOption === 0 ? 'cyan' : 'white'}>
          {selectedOption === 0 ? '→ ' : '  '}[r] Resume where I left off
        </Text>
      </Box>

      <Box>
        <Text color={selectedOption === 1 ? 'cyan' : 'white'}>
          {selectedOption === 1 ? '→ ' : '  '}[f] Start fresh research
        </Text>
      </Box>

      <Box marginTop={1}>
        <Text color="gray">
          Use ↑↓ arrows or r/f keys to select, Enter to confirm
        </Text>
      </Box>
    </Box>
  );
};

// Keyboard Hints for CLI
const CLIKeyboardHints: React.FC = () => {
  return (
    <Box flexDirection="column" borderStyle="single" borderColor="gray" padding={1}>
      <Text color="gray" bold>Keyboard Shortcuts:</Text>
      <Text color="gray">[b] Request break  [c] Continue  [Esc] Cancel</Text>
    </Box>
  );
};

// Simple CLI Research Status
export const CLIResearchStatus: React.FC<{
  isActive: boolean;
  currentQuery: string;
  timeElapsed: number;
}> = ({ isActive, currentQuery, timeElapsed }) => {
  const [spinner, setSpinner] = useState(0);
  const spinnerChars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setSpinner(prev => (prev + 1) % spinnerChars.length);
    }, 100);

    return () => clearInterval(interval);
  }, [isActive]);

  if (!isActive) {
    return (
      <Box>
        <Text color="green">✅ Research completed</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      <Box>
        <Text color="blue">{spinnerChars[spinner]} Researching...</Text>
        <Text color="gray"> ({Math.round(timeElapsed)}m elapsed)</Text>
      </Box>
      <Box marginLeft={3}>
        <Text color="white">{currentQuery}</Text>
      </Box>
    </Box>
  );
};

export {
  CLIProgressBar,
  CLICurrentActivity,
  CLITimeAwareness,
  CLIAttentionState,
  CLIBreakPrompt,
  CLIChunkCard,
  CLIKeyboardHints,
  CLIResearchStatus
};