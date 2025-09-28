/**
 * Example: Dopemux CLI Research Command Integration
 *
 * Shows how the React Ink components integrate with a Dopemux CLI command
 */

import React, { useState, useEffect } from 'react';
import { render, Box, Text, useApp } from 'ink';
import { CLIResearchProgress, CLISessionResume, CLIChunkDisplay } from './CLIResearchComponents';
import { ADHDResearchManager } from './adhd-research-manager';
import { DopemuxResearchClient } from './mcp-integration';

// Main CLI Research Command Component
const ResearchCommand: React.FC<{
  query: string;
  options: {
    depth?: 'shallow' | 'medium' | 'deep';
    resume?: string; // session ID to resume
    chunkDuration?: number;
  };
}> = ({ query, options }) => {
  const { exit } = useApp();
  const [researchManager] = useState(() => new ADHDResearchManager({
    chunkDuration: options.chunkDuration || 25,
    enableBreakSuggestions: true,
    enableHyperfocusWarnings: true
  }));

  const [currentView, setCurrentView] = useState<'resume' | 'progress' | 'chunks' | 'complete'>('progress');
  const [progressState, setProgressState] = useState(null);
  const [attentionState, setAttentionState] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [finalReport, setFinalReport] = useState('');

  // Check for resume session
  useEffect(() => {
    if (options.resume) {
      // Load session data (mock)
      setSessionData({
        summary: `You were researching "${query}". Found 3 key insights, completed 2 of 4 research chunks.`,
        timeAway: 45, // minutes
        sessionId: options.resume
      });
      setCurrentView('resume');
    } else {
      startNewResearch();
    }
  }, []);

  // Listen to research manager events
  useEffect(() => {
    researchManager.on('sessionStart', (data) => {
      setCurrentView('progress');
    });

    researchManager.on('chunkStart', (data) => {
      setProgressState(prev => ({
        ...prev,
        currentChunk: data.chunkNumber,
        currentActivity: data.query
      }));
    });

    researchManager.on('chunkProgress', (data) => {
      setProgressState(prev => ({
        ...prev,
        timeSpent: prev.timeSpent + 0.5 // Mock time increment
      }));
    });

    researchManager.on('attentionStateChange', (state) => {
      setAttentionState(state);
    });

    researchManager.on('sessionComplete', (data) => {
      setFinalReport(data.report);
      setCurrentView('complete');
    });

    researchManager.on('breakSuggestion', (data) => {
      // Break suggestion is handled by CLIResearchProgress
    });

    return () => {
      researchManager.removeAllListeners();
    };
  }, [researchManager]);

  const startNewResearch = async () => {
    try {
      // Initialize progress state
      setProgressState({
        currentChunk: 0,
        totalChunks: 3, // Mock chunk count
        completedChunks: [],
        timeSpent: 0,
        estimatedTimeRemaining: 30,
        currentActivity: 'Initializing research...'
      });

      setAttentionState({
        type: 'optimal',
        energy: 80,
        timeInState: 0,
        lastBreak: new Date()
      });

      // Start research (this would integrate with actual GPT-Researcher)
      const report = await researchManager.startResearch(query, {
        depth: options.depth || 'medium'
      });

      setFinalReport(report);
      setCurrentView('complete');
    } catch (error) {
      console.error('Research failed:', error);
      exit();
    }
  };

  const handleResumeSession = () => {
    setCurrentView('progress');
    // Continue research from where left off
    startNewResearch();
  };

  const handleStartFresh = () => {
    setCurrentView('progress');
    startNewResearch();
  };

  const handleBreakRequested = () => {
    // Pause research and show break timer
    setProgressState(prev => ({
      ...prev,
      currentActivity: 'Taking a break...'
    }));
  };

  const handleContinue = () => {
    // Resume research
    setProgressState(prev => ({
      ...prev,
      currentActivity: 'Resuming research...'
    }));
  };

  // Render different views based on current state
  switch (currentView) {
    case 'resume':
      return (
        <CLISessionResume
          sessionSummary={sessionData.summary}
          timeAway={sessionData.timeAway}
          onResume={handleResumeSession}
          onStartFresh={handleStartFresh}
        />
      );

    case 'progress':
      return (
        <CLIResearchProgress
          progress={progressState}
          attentionState={attentionState}
          onBreakRequested={handleBreakRequested}
          onContinue={handleContinue}
        />
      );

    case 'chunks':
      return (
        <CLIChunkDisplay
          chunks={[]} // Would come from research manager
          currentChunkIndex={progressState?.currentChunk || 0}
        />
      );

    case 'complete':
      return <ResearchComplete report={finalReport} onExit={() => exit()} />;

    default:
      return (
        <Box>
          <Text color="red">Unknown view state</Text>
        </Box>
      );
  }
};

// Research Complete View
const ResearchComplete: React.FC<{
  report: string;
  onExit: () => void;
}> = ({ report, onExit }) => {
  const [showFullReport, setShowFullReport] = useState(false);

  useInput((input, key) => {
    if (input === 'r') {
      setShowFullReport(!showFullReport);
    }
    if (input === 'q' || key.escape) {
      onExit();
    }
  });

  const reportPreview = report.slice(0, 300) + (report.length > 300 ? '...' : '');

  return (
    <Box flexDirection="column" padding={1}>
      <Text color="green" bold>✅ Research Complete!</Text>
      <Box marginTop={1}>
        <Text color="cyan">Research Summary:</Text>
      </Box>

      <Box marginTop={1} marginLeft={2}>
        <Text color="white">
          {showFullReport ? report : reportPreview}
        </Text>
      </Box>

      <Box marginTop={2}>
        <Text color="gray">
          [r] Toggle full report  [q] Exit
        </Text>
      </Box>
    </Box>
  );
};

// CLI Command Entry Point
export const createResearchCommand = () => {
  return (query: string, options: any) => {
    const { unmount } = render(
      <ResearchCommand query={query} options={options} />
    );

    // Return cleanup function
    return unmount;
  };
};

// Example usage in Dopemux CLI
/*
// In your Dopemux CLI command definition:

import { createResearchCommand } from './cli-usage-example';

const researchCommand = createResearchCommand();

// CLI command handler
export const research = async (query: string, options: {
  depth?: 'shallow' | 'medium' | 'deep';
  resume?: string;
  chunks?: number;
}) => {
  // Start the React Ink UI
  const cleanup = researchCommand(query, {
    depth: options.depth,
    resume: options.resume,
    chunkDuration: options.chunks || 25
  });

  // The UI will handle the research process
  // cleanup() can be called to unmount the UI
};

// CLI usage examples:
// dopemux research "AI development trends 2024"
// dopemux research "quantum computing" --depth=deep
// dopemux research --resume=session-123
// dopemux research "competitive analysis" --chunks=15
*/

export default ResearchCommand;