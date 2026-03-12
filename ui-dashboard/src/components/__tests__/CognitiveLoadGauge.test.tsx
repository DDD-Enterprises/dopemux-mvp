import { render, screen } from '@testing-library/react';
import CognitiveLoadGauge from '../CognitiveLoadGauge';

describe('CognitiveLoadGauge', () => {
  it('renders correctly with "low" status', () => {
    render(
      <CognitiveLoadGauge
        load={0.2}
        status="low"
        recommendation="Take on more tasks"
      />
    );

    // Status label
    expect(screen.getByText(/Low Load/)).toBeInTheDocument();

    // Load percentage (20%)
    expect(screen.getByText('20%')).toBeInTheDocument();

    // Recommendation
    expect(screen.getByText('Recommendation:')).toBeInTheDocument();
    expect(screen.getByText('Take on more tasks')).toBeInTheDocument();

    // Roast text for non-critical status
    expect(screen.getByText(/log your restraint/)).toBeInTheDocument();
  });

  it('renders correctly with "optimal" status', () => {
    render(
      <CognitiveLoadGauge
        load={0.5}
        status="optimal"
        recommendation="Keep going"
      />
    );

    expect(screen.getByText(/Optimal Zone/)).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('Keep going')).toBeInTheDocument();
  });

  it('renders correctly with "high" status', () => {
    render(
      <CognitiveLoadGauge
        load={0.8}
        status="high"
        recommendation="Delegate tasks"
      />
    );

    expect(screen.getByText(/High Load/)).toBeInTheDocument();
    expect(screen.getByText('80%')).toBeInTheDocument();
    expect(screen.getByText('Delegate tasks')).toBeInTheDocument();
  });

  it('renders correctly with "critical" status', () => {
    render(
      <CognitiveLoadGauge
        load={0.95}
        status="critical"
        recommendation="Stop immediately"
      />
    );

    expect(screen.getByText(/Critical Load/)).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('Stop immediately')).toBeInTheDocument();

    // Roast text for critical status
    expect(screen.getByText(/You're cooked/)).toBeInTheDocument();
  });
});
