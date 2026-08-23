// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, test } from 'vitest';

import RepositoryPlannerPage from '../RepositoryPlannerPage';
import { loadExtensions } from '../extensionRegistry';

afterEach(cleanup);

describe('RepositoryPlannerPage', () => {
  test('renders the three source projections and explicit non-authority', () => {
    render(<RepositoryPlannerPage />);

    expect(screen.getByRole('heading', { name: 'Repository merge planner' })).toBeVisible();
    expect(screen.getByText('dopemux-mvp')).toBeVisible();
    expect(screen.getByText('adOps')).toBeVisible();
    expect(screen.getByText('dnh-crm')).toBeVisible();
    expect(screen.getByText('Ready for Control Tower review')).toBeVisible();
    expect(screen.getByText('Blocked: conflicting evidence')).toBeVisible();
    expect(screen.getByText('Deferred: stale evidence')).toBeVisible();
    expect(screen.getByText('Unknown evidence: audit_state')).toBeVisible();
    expect(screen.getByText(/Authority: NONE/)).toBeVisible();
    expect(screen.getByText(/Projection only/)).toBeVisible();
  });

  test('opens accessible lane details, provenance, and returns focus on close', () => {
    render(<RepositoryPlannerPage />);
    const trigger = screen.getByRole('button', { name: /Inspect adOps legacy-corpus-rating-002/ });

    trigger.focus();
    fireEvent.click(trigger);
    expect(screen.getByRole('dialog', { name: /adOps.*legacy-corpus-rating-002/i })).toBeVisible();
    expect(screen.getByText('REMOTE_COMMIT_ABSENT')).toBeVisible();
    expect(screen.getByText('Observed head')).toBeVisible();
    expect(screen.getAllByText(/SHA-256/).length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: 'Blocking conflicts' })).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: 'Close lane details' }));
    expect(trigger).toHaveFocus();
  });

  test('contains no authority or network controls', () => {
    render(<RepositoryPlannerPage />);
    expect(screen.queryByRole('button', { name: /merge|approve|accept|activate|refresh/i })).toBeNull();
    expect(screen.queryByRole('link')).toBeNull();
  });
});

describe('extension registry', () => {
  test('sorts valid extensions by bytewise identifier', () => {
    const extensions = loadExtensions({
      './extensions/zeta.tsx': { default: { id: 'zeta', render: () => null } },
      './extensions/alpha.tsx': { default: { id: 'alpha', render: () => null } },
    });
    expect(extensions.map((extension) => extension.id)).toEqual(['alpha', 'zeta']);
  });

  test('fails closed for duplicate and malformed exports', () => {
    expect(() =>
      loadExtensions({
        './extensions/a.tsx': { default: { id: 'same', render: () => null } },
        './extensions/b.tsx': { default: { id: 'same', render: () => null } },
      }),
    ).toThrow(/duplicate/i);
    expect(() => loadExtensions({ './extensions/bad.tsx': { default: { id: '', render: 'no' } } })).toThrow(
      /malformed/i,
    );
  });
});
