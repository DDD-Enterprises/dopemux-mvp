import { expect, test } from 'vitest';

import {
  getCompletionTransitionTask,
  getSkipTransitionTask,
  type SequencerTransitionTask,
} from '../taskSequencerTransitions';

interface TestTask extends SequencerTransitionTask {
  title: string;
}

const tasks: TestTask[] = [
  { id: '1', title: 'Current', status: 'in_progress' },
  { id: '2', title: 'Medium follow-up', status: 'pending' },
  { id: '3', title: 'Low follow-up', status: 'pending' },
];

test('completion transition mirrors the sequencer completion action', () => {
  const optimizedTasks = [tasks[2], tasks[1], tasks[0]];

  expect(getCompletionTransitionTask('1', tasks, optimizedTasks)?.id).toBe('3');
});

test('completion transition falls back to remaining task order when optimized state is stale', () => {
  const optimizedTasks = [tasks[0]];

  expect(getCompletionTransitionTask('1', tasks, optimizedTasks)?.id).toBe('2');
});

test('completion transition returns null when the current task is the final incomplete task', () => {
  const finalTaskState = [
    { id: '1', title: 'Current', status: 'in_progress' },
    { id: '2', title: 'Completed', status: 'completed' },
  ] satisfies TestTask[];

  expect(getCompletionTransitionTask('1', finalTaskState, [finalTaskState[0]])).toBeNull();
});

test('skip transition mirrors the sequencer skip action and wraps to the first task', () => {
  const optimizedTasks = [tasks[2], tasks[1], tasks[0]];

  expect(getSkipTransitionTask('3', optimizedTasks)?.id).toBe('2');
  expect(getSkipTransitionTask('1', optimizedTasks)?.id).toBe('3');
});

test('skip transition returns null when there is no other task to skip to', () => {
  expect(getSkipTransitionTask('1', [tasks[0]])).toBeNull();
});
