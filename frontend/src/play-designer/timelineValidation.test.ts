import type { PlayDesign } from '../types';
import { timelineIntegrityIssues } from './timelineValidation';

const base: PlayDesign = {
  id: 'TIMELINE-VALIDATION',
  unit: 'offense',
  timeline: { duration_ms: 1000, events: [] },
  players: [{ id: 'QB', position: 'QB', start: { x: 50, y: 38 } }],
  elements: [{ id: 'ROUTE', kind: 'route', player_id: 'QB', points: [{ x: 50, y: 38 }, { x: 50, y: 20 }], timing: { start_ms: 0, end_ms: 800, phases: [{ id: 'stem', label: 'Stem', start_ms: 0, end_ms: 400 }, { id: 'break', label: 'Break', start_ms: 350, end_ms: 700 }] } }],
};

describe('timeline integrity validation', () => {
  it('finds stale references, duplicate IDs, invalid windows, and branch mismatches', () => {
    const design: PlayDesign = { ...base, elements: [{ ...base.elements![0], branches: [{ id: 'OUT', label: 'Out', condition: 'If leverage changes', points: [{ x: 50, y: 20 }, { x: 70, y: 20 }] }] }], timeline: { duration_ms: 1000, events: [
      { id: 'DUP', kind: 'read', element_id: 'MISSING', player_id: 'NOPE', start_ms: 900, end_ms: 1200 },
      { id: 'DUP', kind: 'read', element_id: 'ROUTE', branch_id: 'NOT-A-BRANCH', start_ms: 400, end_ms: 200 },
    ] } };
    const codes = timelineIntegrityIssues(design).map((issue) => issue.code);
    expect(codes).toEqual(expect.arrayContaining(['TIMELINE_EVENT_ID_DUPLICATE', 'TIMELINE_ELEMENT_MISSING', 'TIMELINE_PLAYER_MISSING', 'TIMELINE_END_OUT_OF_RANGE', 'TIMELINE_BRANCH_MISSING', 'TIMELINE_WINDOW_INVALID', 'TIMELINE_PHASE_OVERLAP']));
  });

  it('accepts synchronized events and non-overlapping phases inside the play clock', () => {
    const design: PlayDesign = { ...base, elements: [{ ...base.elements![0], timing: { start_ms: 0, end_ms: 800, phases: [{ id: 'stem', label: 'Stem', start_ms: 0, end_ms: 400 }, { id: 'break', label: 'Break', start_ms: 400, end_ms: 700 }] } }], timeline: { duration_ms: 1000, events: [{ id: 'READ', kind: 'read', element_id: 'ROUTE', player_id: 'QB', start_ms: 300, end_ms: 500 }] } };
    expect(timelineIntegrityIssues(design)).toEqual([]);
  });
});
