/**
 * DeepContextViewer - Tier 3 Component
 * Complete decision analysis with NO ADHD limits
 *
 * Features:
 * - Full summary + rationale + implementation
 * - Cognitive load indicator (magenta)
 * - All relationships with type badges
 * - Related decisions list
 * - Total network statistics
 */

import React, {useState, useEffect} from 'react';
import {Box, Text, useInput} from 'ink';
import {kgClient} from '../api/client';
import type {FullDecisionContext} from '../types';

interface Props {
  decisionId: number;
  onBack: () => void;
}

export const DeepContextViewer: React.FC<Props> = ({decisionId, onBack}) => {
  const [context, setContext] = useState<FullDecisionContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load full context on mount
  useEffect(() => {
    setLoading(true);
    setError(null);

    kgClient.getFullContext(decisionId)
      .then(data => {
        setContext(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load context:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [decisionId]);

  // Keyboard controls
  useInput((input) => {
    if (input === 'b') {
      onBack();
    }

    if (input === 'q') {
      process.exit(0);
    }
  });

  // Loading state
  if (loading) {
    return (
      <Box padding={1}>
        <Text>Loading full context...</Text>
      </Box>
    );
  }

  // Error state
  if (error || !context) {
    return (
      <Box padding={1} flexDirection="column">
        <Text color="red" bold>Error loading context</Text>
        <Text>{error || 'Unknown error'}</Text>
        <Text dimColor marginTop={1}>Press 'b' to go back</Text>
      </Box>
    );
  }

  // Main view
  return (
    <Box flexDirection="column" padding={1}>
      <Text color="green" bold>
        Deep Context - Decision #{decisionId}
      </Text>

      <Text dimColor marginTop={0}>
        b: Back | q: Quit
      </Text>

      {/* Decision Summary */}
      <Box marginTop={1} flexDirection="column">
        <Text bold>{context.decision.summary}</Text>
      </Box>

      {/* Cognitive Load Indicator */}
      <Box marginTop={1}>
        <Text color="magenta" bold>
          Cognitive Load: {context.cognitive_load.toUpperCase()}
        </Text>
      </Box>

      {/* Rationale Section */}
      {context.decision.rationale && (
        <Box marginTop={1} flexDirection="column">
          <Text color="cyan" bold>Rationale:</Text>
          <Box marginLeft={2}>
            <Text>
              {context.decision.rationale.slice(0, 200)}
              {context.decision.rationale.length > 200 ? '...' : ''}
            </Text>
          </Box>
        </Box>
      )}

      {/* Implementation Section */}
      {context.decision.implementation && (
        <Box marginTop={1} flexDirection="column">
          <Text color="cyan" bold>Implementation:</Text>
          <Box marginLeft={2}>
            <Text>
              {context.decision.implementation.slice(0, 200)}
              {context.decision.implementation.length > 200 ? '...' : ''}
            </Text>
          </Box>
        </Box>
      )}

      {/* Relationships Section */}
      <Box marginTop={1} flexDirection="column">
        <Text color="cyan" bold>
          Relationships ({context.direct_relationships.length}):
        </Text>

        {context.direct_relationships.length > 0 ? (
          context.direct_relationships.map((rel, i) => (
            <Box key={i} marginLeft={2}>
              <Text>
                <Text bold>#{rel.source_id}</Text>
                {' →['}
                <Text color="yellow">{rel.type}</Text>
                {']→ '}
                <Text bold>#{rel.target_id}</Text>
              </Text>
            </Box>
          ))
        ) : (
          <Box marginLeft={2}>
            <Text dimColor>No relationships</Text>
          </Box>
        )}
      </Box>

      {/* Related Decisions Summary */}
      <Box marginTop={1} flexDirection="column">
        <Text>
          Related decisions: {context.related_decisions.length}
        </Text>
        <Text>
          Total network: {context.total_related}
        </Text>
      </Box>

      {/* Tags (if available) */}
      {context.decision.tags && context.decision.tags.length > 0 && (
        <Box marginTop={1}>
          <Text dimColor>
            Tags: {context.decision.tags.join(', ')}
          </Text>
        </Box>
      )}
    </Box>
  );
};
