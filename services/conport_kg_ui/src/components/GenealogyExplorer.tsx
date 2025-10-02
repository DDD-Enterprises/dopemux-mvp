/**
 * GenealogyExplorer - Tier 2 Component
 * Progressive disclosure: 1-hop → 2-hop expansion
 *
 * Features:
 * - Shows decision + immediate neighbors
 * - Press 'e' to expand to 2-hop
 * - Visual hop indicators (→ and ⇒)
 * - Press 'f' for full context view
 */

import React, {useState, useEffect} from 'react';
import {Box, Text, useInput} from 'ink';
import {kgClient} from '../api/client';
import type {DecisionNeighborhood} from '../types';

interface Props {
  decisionId: number;
  onBack: () => void;
  onFullContext: (id: number) => void;
}

export const GenealogyExplorer: React.FC<Props> = ({
  decisionId,
  onBack,
  onFullContext
}) => {
  const [neighborhood, setNeighborhood] = useState<DecisionNeighborhood | null>(null);
  const [maxHops, setMaxHops] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load neighborhood (refetch when maxHops changes)
  useEffect(() => {
    setLoading(true);
    setError(null);

    kgClient.getNeighborhood(decisionId, maxHops)
      .then(data => {
        setNeighborhood(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load neighborhood:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [decisionId, maxHops]);

  // Keyboard controls
  useInput((input) => {
    if (input === 'e' && maxHops === 1) {
      setMaxHops(2);  // Expand to 2-hop
    }

    if (input === 'f') {
      onFullContext(decisionId);  // Full context
    }

    if (input === 'b') {
      onBack();  // Back to browser
    }

    if (input === 'q') {
      process.exit(0);
    }
  });

  // Loading state
  if (loading) {
    return (
      <Box padding={1}>
        <Text>Loading genealogy...</Text>
      </Box>
    );
  }

  // Error state
  if (error || !neighborhood) {
    return (
      <Box padding={1} flexDirection="column">
        <Text color="red" bold>Error loading genealogy</Text>
        <Text>{error || 'Unknown error'}</Text>
        <Text dimColor marginTop={1}>Press 'b' to go back</Text>
      </Box>
    );
  }

  // Main view
  return (
    <Box flexDirection="column" padding={1}>
      <Text color="green" bold>
        Genealogy Explorer - Decision #{decisionId}
      </Text>

      <Text dimColor marginTop={0}>
        e: Expand to 2-hop | f: Full Context | b: Back | q: Quit
      </Text>

      {/* Center decision */}
      <Box marginTop={1} flexDirection="column">
        <Text bold>{neighborhood.center.summary}</Text>
      </Box>

      {/* 1-hop neighbors */}
      <Box marginTop={1} flexDirection="column">
        <Text color="cyan">
          1-hop neighbors ({neighborhood.hop_1_neighbors.length}):
        </Text>

        {neighborhood.hop_1_neighbors.map(d => (
          <Box key={d.id} marginLeft={2}>
            <Text>
              → <Text bold>#{d.id}</Text>: {d.summary.slice(0, 50)}
              {d.summary.length > 50 ? '...' : ''}
            </Text>
          </Box>
        ))}

        {neighborhood.hop_1_neighbors.length === 0 && (
          <Box marginLeft={2}>
            <Text dimColor>No direct neighbors</Text>
          </Box>
        )}
      </Box>

      {/* 2-hop neighbors (if expanded) */}
      {maxHops === 2 && neighborhood.hop_2_neighbors.length > 0 && (
        <Box marginTop={1} flexDirection="column">
          <Text color="cyan">
            2-hop neighbors ({neighborhood.hop_2_neighbors.length}):
          </Text>

          {neighborhood.hop_2_neighbors.map(d => (
            <Box key={d.id} marginLeft={4}>
              <Text>
                ⇒ <Text bold>#{d.id}</Text>: {d.summary.slice(0, 45)}
                {d.summary.length > 45 ? '...' : ''}
              </Text>
            </Box>
          ))}
        </Box>
      )}

      {/* Expansion hint */}
      {maxHops === 1 && (
        <Box marginTop={1}>
          <Text color="yellow">
            Press 'e' to expand to 2-hop neighbors
          </Text>
        </Box>
      )}

      {/* Network summary */}
      <Box marginTop={1}>
        <Text dimColor>
          Total network: {neighborhood.total_neighbors} decisions
          {maxHops === 2 ? ' (fully expanded)' : ''}
        </Text>
      </Box>
    </Box>
  );
};
