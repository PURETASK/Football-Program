import type { PlayTimelineEvent } from '../types';

/** Read a timeline event across the legacy API shape and the current editor shape. */
export function timelineEventKind(event: PlayTimelineEvent): string {
  return String(event.kind ?? event.type ?? 'event');
}

/** Read an event's first timestamp across `start_ms`, `ms`, and legacy `at_ms`. */
export function timelineEventStart(event: PlayTimelineEvent): number {
  return Number(event.start_ms ?? event.ms ?? event.at_ms ?? 0);
}

/** Read an event's end timestamp while retaining a safe one-millisecond window. */
export function timelineEventEnd(event: PlayTimelineEvent, fallback: number): number {
  return Math.max(timelineEventStart(event) + 1, Number(event.end_ms ?? fallback));
}

/** Return a canonical editor-safe copy without discarding unknown provider fields. */
export function normalizeTimelineEvent(event: PlayTimelineEvent, fallbackEnd: number): PlayTimelineEvent {
  const start = timelineEventStart(event);
  return {
    ...event,
    kind: timelineEventKind(event),
    start_ms: start,
    end_ms: timelineEventEnd(event, fallbackEnd),
  };
}
