export interface SequencerTransitionTask {
  id: string;
  status: 'pending' | 'in_progress' | 'completed';
}

export const getCompletionTransitionTask = <Task extends SequencerTransitionTask>(
  taskId: string | null,
  allTasks: Task[],
  optimizedTasks: Task[]
): Task | null => {
  if (!taskId) return null;

  const remainingTasks = allTasks.filter(
    (task) => task.id !== taskId && task.status !== 'completed'
  );

  return optimizedTasks.find((task) => task.id !== taskId) ?? remainingTasks[0] ?? null;
};

export const getSkipTransitionTask = <Task extends SequencerTransitionTask>(
  taskId: string | null,
  optimizedTasks: Task[]
): Task | null => {
  if (!taskId || optimizedTasks.length <= 1) return null;

  const currentIndex = optimizedTasks.findIndex((task) => task.id === taskId);
  const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % optimizedTasks.length;

  return optimizedTasks[nextIndex] ?? null;
};
