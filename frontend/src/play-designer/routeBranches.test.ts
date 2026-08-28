import { describe, expect, it } from 'vitest';
import { addRouteBranch, branchProgress, branchStart } from './routeBranches';

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
});
