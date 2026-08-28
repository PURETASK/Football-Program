import type { PlayElement, TimelinePhase } from '../types';

type PhaseTemplate = Array<[id: string, label: string, startRatio: number, endRatio: number]>;

const DEFAULT_PHASES: Record<string, PhaseTemplate> = {
  route: [['release', 'Release', 0, 0.18], ['stem', 'Stem', 0.18, 0.48], ['break', 'Break', 0.48, 0.72], ['finish', 'Finish', 0.72, 1]],
  motion: [['align', 'Align', 0, 0.2], ['travel', 'Travel', 0.2, 0.78], ['settle', 'Settle', 0.78, 1]],
  run: [['mesh', 'Mesh', 0, 0.25], ['track', 'Track', 0.25, 0.72], ['finish', 'Finish', 0.72, 1]],
  block: [['strike', 'Strike', 0, 0.22], ['fit', 'Fit', 0.22, 0.58], ['sustain', 'Sustain', 0.58, 1]],
  coverage: [['pedal', 'Pedal', 0, 0.25], ['match', 'Match', 0.25, 0.72], ['close', 'Close', 0.72, 1]],
  rush: [['getoff', 'Get off', 0, 0.22], ['attack', 'Attack', 0.22, 0.62], ['finish', 'Finish', 0.62, 1]],
  stunt: [['penetrate', 'Penetrate', 0, 0.32], ['exchange', 'Exchange', 0.32, 0.68], ['finish', 'Finish', 0.68, 1]],
  rotation: [['key', 'Key', 0, 0.25], ['rotate', 'Rotate', 0.25, 0.72], ['fit', 'Fit', 0.72, 1]],
  read: [['identify', 'Identify', 0, 0.3], ['confirm', 'Confirm', 0.3, 0.72], ['decide', 'Decide', 0.72, 1]],
  annotation: [['teach', 'Teach', 0, 1]],
};

export function elementTiming(element: PlayElement, fallbackEnd = 1200): { start: number; end: number } {
  const start = Number(element.timing?.start_ms ?? element.start_ms ?? 0);
  const end = Math.max(start + 1, Number(element.timing?.end_ms ?? element.end_ms ?? fallbackEnd));
  return { start, end };
}

export function defaultTimelinePhases(kind: string, start: number, end: number): TimelinePhase[] {
  const template = DEFAULT_PHASES[kind] ?? DEFAULT_PHASES.annotation;
  const span = Math.max(1, end - start);
  return template.map(([id, label, startRatio, endRatio]) => {
    const phaseStart = Math.round(start + span * startRatio);
    return { id, label, start_ms: phaseStart, end_ms: Math.max(phaseStart + 1, Math.round(start + span * endRatio)) };
  });
}

export function timingPatch(element: PlayElement, nextStart: number, nextEnd: number): Partial<PlayElement> {
  const start = Math.max(-5000, Math.round(nextStart));
  const end = Math.max(start + 1, Math.round(nextEnd));
  const current = elementTiming(element);
  const phases = element.timing?.phases?.length
    ? element.timing.phases.map((phase) => {
        const oldSpan = Math.max(1, current.end - current.start);
        const nextSpan = end - start;
        const phaseStart = Math.round(start + ((phase.start_ms - current.start) / oldSpan) * nextSpan);
        const phaseEnd = Math.round(start + ((phase.end_ms - current.start) / oldSpan) * nextSpan);
        return { ...phase, start_ms: phaseStart, end_ms: Math.max(phaseStart + 1, phaseEnd) };
      })
    : defaultTimelinePhases(element.kind, start, end);
  return { start_ms: start, end_ms: end, timing: { ...element.timing, start_ms: start, end_ms: end, phases } };
}

export function phaseAtTime(element: PlayElement, ms: number): TimelinePhase | undefined {
  const timing = elementTiming(element);
  const phases = element.timing?.phases?.length ? element.timing.phases : defaultTimelinePhases(element.kind, timing.start, timing.end);
  return phases.find((phase) => ms >= phase.start_ms && ms <= phase.end_ms);
}
