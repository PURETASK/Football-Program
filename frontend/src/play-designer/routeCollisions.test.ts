import { describe, expect, it } from 'vitest';
import { routeCollisions } from './geometry';

describe('route collision explanations', () => {
  it('reports an accidental overlapping route pair', () => {
    const result = routeCollisions([{ id: 'A', kind: 'route', points: [{ x: 10, y: 10 }, { x: 90, y: 40 }] }, { id: 'B', kind: 'route', points: [{ x: 90, y: 10 }, { x: 10, y: 40 }] }]);
    expect(result[0]).toMatchObject({ firstId: 'A', secondId: 'B', intentional: false });
    expect(result[0].explanation).toContain('separate');
    expect(result[0].kind).toBe('intersection');
  });
  it('recognizes an intentional crossing only when both routes opt in', () => {
    const result = routeCollisions([{ id: 'A', kind: 'route', collision_intent: 'intentional', points: [{ x: 10, y: 10 }, { x: 90, y: 40 }] }, { id: 'B', kind: 'route', collision_intent: 'intentional', points: [{ x: 90, y: 10 }, { x: 10, y: 40 }] }]);
    expect(result[0]).toMatchObject({ intentional: true });
    expect(result[0].explanation).toContain('intentional crossing');
  });

  it('uses the wider configured corridor for close routes', () => {
    const result = routeCollisions([
      { id: 'A', kind: 'route', collision_corridor_yards: 0.5, points: [{ x: 10, y: 10 }, { x: 90, y: 10 }] },
      { id: 'B', kind: 'route', collision_corridor_yards: 2, points: [{ x: 10, y: 12 }, { x: 90, y: 12 }] },
    ]);
    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ kind: 'corridor', corridorThreshold: 2, minimumSeparation: 2 });
  });
});
