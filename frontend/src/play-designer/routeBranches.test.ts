import { describe, expect, it } from 'vitest';
import { addRouteBranch, branchProgress, branchStart, playbackPathForElement, playbackPathStateForElement } from './routeBranches';

describe('branchable route authoring', () => {
  it('anchors a new alternate path to the primary finish', () => {
    const element = { id: 'R1', kind: 'route', points: [{ x: 20, y: 30 }, { x: 30, y: 10 }] };
    expect(branchStart(element)).toEqual({ x: 30, y: 10 });
    expect(addRouteBranch(element, { label: 'Convert out', condition: 'If corner squats', points: [{ x: 30, y: 10 }, { x: 42, y: 12 }] })).toEqual([expect.objectContaining({ label: 'Convert out', condition: 'If corner squats', points: [{ x: 30, y: 10 }, { x: 42, y: 12 }] })]);
  });
  it('reveals an alternate path over its own timing window', () => {
    expect(branchProgress({ start_ms: 500, end_ms: 1500 }, 0)).toBe(0);
    expect(branchProgress({ start_ms: 500, end_ms: 1500 }, 1000)).toBe(0.5);
    expect(branchProgress({ start_ms: 500, end_ms: 1500 }, 1600)).toBe(1);
  });
  it('resolves a branch-aware playback event to the executable alternate polyline', () => {
    const element = {
      id: 'ROUTE-X',
      kind: 'route' as const,
      points: [{ x: 10, y: 30 }, { x: 30, y: 10 }],
      branches: [{ id: 'BR-ALERT', label: 'Alert', condition: 'If rotation', points: [{ x: 30, y: 10 }, { x: 50, y: 12 }] }],
    };
    const event = { id: 'READ-1', kind: 'read', element_id: 'ROUTE-X', branch_id: 'BR-ALERT', start_ms: 500, end_ms: 900 };
    expect(playbackPathForElement(element, 300, [event])).toEqual(element.points);
    expect(playbackPathForElement(element, 700, [event])).toEqual(element.branches[0].points);
    expect(playbackPathForElement(element, 700, [])).toEqual(element.points);
    expect(playbackPathStateForElement(element, 700, [event])).toMatchObject({ start: 500, end: 900, branchId: 'BR-ALERT' });
  });
});
