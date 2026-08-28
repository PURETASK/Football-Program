import type { PlayElement, Point } from '../types';

export interface RouteBranchInput { label: string; condition: string; points: Point[]; start_ms?: number; end_ms?: number; }

export function addRouteBranch(element: PlayElement, branch: RouteBranchInput): PlayElement['branches'] {
  return [...(element.branches ?? []), { id: `${element.id}-BRANCH-${Date.now().toString(36).toUpperCase()}`, ...branch }];
}

export function branchStart(element: PlayElement): Point | undefined {
  return (element.points ?? element.path ?? []).at(-1);
}

export function branchProgress(branch: { start_ms?: number; end_ms?: number; timing?: { start_ms?: number; end_ms?: number } }, timeMs: number, fallbackEnd = 3000): number {
  const start = Number(branch.start_ms ?? branch.timing?.start_ms ?? 0);
  const end = Number(branch.end_ms ?? branch.timing?.end_ms ?? fallbackEnd);
  if (timeMs <= start) return 0;
  if (timeMs >= end) return 1;
  return (timeMs - start) / Math.max(1, end - start);
}
