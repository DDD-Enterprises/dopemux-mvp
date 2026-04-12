/**
 * App - Main routing component
 * State machine for navigating between Browser → Explorer → Viewer
 *
 * Flow:
 * - Start: DecisionBrowser (Top-3)
 * - Select decision: GenealogyExplorer (progressive)
 * - Press 'f': DeepContextViewer (complete)
 * - Press 'b': Back to previous view
 */

import React, {useState} from 'react';
import {DecisionBrowser} from './components/DecisionBrowser';
import {GenealogyExplorer} from './components/GenealogyExplorer';
import {DeepContextViewer} from './components/DeepContextViewer';

type View = 'browser' | 'explorer' | 'viewer';

export const App: React.FC = () => {
  const [view, setView] = useState<View>('browser');
  const [selectedDecisionId, setSelectedDecisionId] = useState<number | null>(null);

  // Navigation: Browser → Explorer
  const handleSelectDecision = (id: number) => {
    setSelectedDecisionId(id);
    setView('explorer');
  };

  // Navigation: Explorer → Viewer
  const handleViewFullContext = (id: number) => {
    setSelectedDecisionId(id);
    setView('viewer');
  };

  // Navigation: Back to Browser
  const handleBackToBrowser = () => {
    setView('browser');
    setSelectedDecisionId(null);
  };

  // Navigation: Back to Explorer
  const handleBackToExplorer = () => {
    setView('explorer');
  };

  // Render based on current view
  if (view === 'browser') {
    return <DecisionBrowser onSelect={handleSelectDecision} />;
  }

  if (view === 'explorer' && selectedDecisionId) {
    return (
      <GenealogyExplorer
        decisionId={selectedDecisionId}
        onBack={handleBackToBrowser}
        onFullContext={handleViewFullContext}
      />
    );
  }

  if (view === 'viewer' && selectedDecisionId) {
    return (
      <DeepContextViewer
        decisionId={selectedDecisionId}
        onBack={handleBackToExplorer}
      />
    );
  }

  // Fallback to browser
  return <DecisionBrowser onSelect={handleSelectDecision} />;
};
