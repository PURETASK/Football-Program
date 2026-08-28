import type { DeliveryTask } from '../types';

export interface DeliveryAgendaGroup {
  key: string;
  label: string;
  tasks: DeliveryTask[];
  openCount: number;
  overdueCount: number;
}

function isComplete(task: DeliveryTask): boolean {
  return task.status === 'completed' || task.status === 'complete' || task.computed_state === 'completed';
}

function isOverdue(task: DeliveryTask, now: number): boolean {
  if (isComplete(task) || !task.due_at) return false;
  const due = Date.parse(task.due_at);
  return Number.isFinite(due) && due < now;
}

export function buildDeliveryAgenda(tasks: DeliveryTask[], now = Date.now()): DeliveryAgendaGroup[] {
  const groups = new Map<string, DeliveryAgendaGroup>();
  for (const task of tasks) {
    const parsed = task.due_at ? new Date(task.due_at) : null;
    const key = parsed && !Number.isNaN(parsed.getTime()) ? parsed.toISOString().slice(0, 10) : 'unscheduled';
    const label = key === 'unscheduled' ? 'Unscheduled' : new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'short', day: 'numeric' }).format(parsed!);
    const group = groups.get(key) ?? { key, label, tasks: [], openCount: 0, overdueCount: 0 };
    group.tasks.push(task);
    if (!isComplete(task)) group.openCount += 1;
    if (isOverdue(task, now)) group.overdueCount += 1;
    groups.set(key, group);
  }
  return [...groups.values()].sort((left, right) => left.key === 'unscheduled' ? 1 : right.key === 'unscheduled' ? -1 : left.key.localeCompare(right.key)).map((group) => ({
    ...group,
    tasks: [...group.tasks].sort((left, right) => (Date.parse(left.due_at || '') || Number.MAX_SAFE_INTEGER) - (Date.parse(right.due_at || '') || Number.MAX_SAFE_INTEGER)),
  }));
}
