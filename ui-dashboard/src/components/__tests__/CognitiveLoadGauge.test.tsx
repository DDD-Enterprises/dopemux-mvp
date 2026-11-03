// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import React from 'react';
import CognitiveLoadGauge from '../CognitiveLoadGauge';

describe('CognitiveLoadGauge micro-UX enhancements', () => {
  const originalClipboard = navigator.clipboard;

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    Object.defineProperty(navigator, 'clipboard', {
      value: originalClipboard,
      writable: true,
      configurable: true,
    });
  });

  it('renders keyboard hint in tooltip title and aria-label', () => {
    render(
      <CognitiveLoadGauge
        load={0.5}
        status="optimal"
        recommendation="Take a brief breather"
      />
    );

    const buttons = screen.getAllByRole('button');
    const button = buttons[0];
    expect(button).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Click or press Enter/Space to copy')
    );
  });

  it('triggers copy on Enter or Space key and resets on Escape key press', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      writable: true,
      configurable: true,
    });

    render(
      <CognitiveLoadGauge
        load={0.5}
        status="optimal"
        recommendation="Take a brief breather"
      />
    );

    const button = screen.getAllByRole('button')[0];

    await act(async () => {
      fireEvent.keyDown(button, { key: 'Enter' });
    });

    expect(writeTextMock).toHaveBeenCalledWith(
      'Load: 50% (Flow Ritual) - AI: Take a brief breather'
    );

    const copiedButton = screen.getAllByRole('button')[0];
    expect(copiedButton).toHaveAttribute('aria-label', 'Copied');

    // Press Escape to cancel copied state
    await act(async () => {
      fireEvent.keyDown(copiedButton, { key: 'Escape' });
    });

    expect(screen.getAllByRole('button')[0]).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Click or press Enter/Space to copy')
    );
  });
});
