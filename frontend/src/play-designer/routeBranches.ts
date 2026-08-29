import type { PlayElement, PlayTimelineEvent, Point } from '../types';
import { timelineEventEnd, timelineEventStart } from './timelineEvents';

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

/** Resolve the executable polyline for an assignment at one playback instant. */
export function playbackPathForElement(element: PlayElement, timeMs: number | null, events: PlayTimelineEvent[] = []): Point[] {
  return playbackPathStateForElement(element, timeMs, events).points;
}

/** Resolve both the executable polyline and its active timing window. */
export function playbackPathStateForElement(element: PlayElement, timeMs: number | null, events: PlayTimelineEvent[] = []): { points: Point[]; start: number; end: number; branchId?: string } {
  const primary = element.points ?? element.path ?? [];
  const primaryStart = Number(element.timing?.start_ms ?? element.start_ms ?? 0);
  const primaryEnd = Math.max(primaryStart + 1, Number(element.timing?.end_ms ?? element.end_ms ?? 3000));
  if (timeMs === null || !element.branches?.length) return { points: primary, start: primaryStart, end: primaryEnd };
  const branchEvent = events
    .filter((event) => event.element_id === element.id && event.branch_id)
    .filter((event) => {
      const start = timelineEventStart(event);
      const end = timelineEventEnd(event, Number(element.timing?.end_ms ?? element.end_ms ?? 3000));
      return timeMs >= start && timeMs <= end;
    })
    .at(-1);
  if (!branchEvent?.branch_id) return { points: primary, start: primaryStart, end: primaryEnd };
  const branch = element.branches.find((candidate) => candidate.id === branchEvent.branch_id);
  if (!branch) return { points: primary, start: primaryStart, end: primaryEnd };
  const start = timelineEventStart(branchEvent);
  const end = timelineEventEnd(branchEvent, primaryEnd);
  return { points: branch.points ?? primary, start, end, branchId: branch.id };
}
