/**
 * DecisionBrowser - Tier 1 Component
 * ADHD-optimized Top-3 pattern for recent decisions
 *
 * Features:
 * - Shows 3 most recent decisions
 * - Arrow key navigation
 * - Green theme for engagement
 * - Cyan selection indicator
 */

import React, {useState, useEffect} from 'react';
import {Box, Text, useInput} from 'ink';
import {kgClient} from '../api/client';
import type {DecisionCard} from '../types';

interface Props {
  onSelect: (id: number) => void;
}

export const DecisionBrowser: React.FC<Props> = ({onSelect}) => {
  const [decisions, setDecisions] = useState<DecisionCard[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load decisions on mount
  useEffect(() => {
    kgClient.getRecentDecisions(3)
      .then(data => {
        setDecisions(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load decisions:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Keyboard navigation
  useInput((input, key) => {
    if (key.upArrow) {
      setSelected(s => Math.max(0, s - 1));
    }

    if (key.downArrow) {
      setSelected(s => Math.min(decisions.length - 1, s + 1));
    }

    if (key.return && decisions.length > 0) {
      onSelect(decisions[selected].id);
    }

    if (input === 'q') {
      process.exit(0);
    }
  });

  // Loading state
  if (loading) {
    return (
      <Box padding={1}>
        <Text>Loading decisions...</Text>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box padding={1} flexDirection="column">
        <Text color="red" bold>Error loading decisions</Text>
        <Text>{error}</Text>
        <Text dimColor marginTop={1}>
          Make sure Integration Bridge is running on port 3016
        </Text>
      </Box>
    );
  }

  // Main view
  return (
    <Box flexDirection="column" padding={1}>
      <Text color="green" bold>
        Decision Browser (Top-3 ADHD Pattern)
      </Text>

      <Text dimColor marginTop={0}>
        Navigate: ↑↓ | Select: Enter | Quit: q
      </Text>

      <Box flexDirection="column" marginTop={1}>
        {decisions.map((d, i) => (
          <Box key={d.id} marginY={1}>
            <Text color={selected === i ? 'cyan' : 'white'}>
              {selected === i ? '▸ ' : '  '}
              <Text bold>#{d.id}</Text>
              {': '}
              {d.summary.slice(0, 60)}
              {d.summary.length > 60 ? '...' : ''}
            </Text>
          </Box>
        ))}
      </Box>

      {decisions.length === 0 && (
        <Box marginTop={1}>
          <Text color="yellow">No decisions found</Text>
        </Box>
      )}

      {decisions.length > 0 && (
        <Box marginTop={1}>
          <Text dimColor>
            Showing {decisions.length} of {decisions.length} recent decisions
          </Text>
        </Box>
      )}
    </Box>
  );
};
