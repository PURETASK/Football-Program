import { describe, expect, it } from 'vitest';
import { routeCollisions } from './geometry';

describe('route collision explanations', () => {
  it('reports an accidental overlapping route pair', () => {
    const result = routeCollisions([{ id: 'A', kind: 'route', points: [{ x: 10, y: 10 }, { x: 90, y: 40 }] }, { id: 'B', kind: 'route', points: [{ x: 90, y: 10 }, { x: 10, y: 40 }] }]);
    expect(result[0]).toMatchObject({ firstId: 'A', secondId: 'B', intentional: false });
    expect(result[0].explanation).toContain('separate');
  });
  it('recognizes an intentional crossing only when both routes opt in', () => {
    const result = routeCollisions([{ id: 'A', kind: 'route', collision_intent: 'intentional', points: [{ x: 10, y: 10 }, { x: 90, y: 40 }] }, { id: 'B', kind: 'route', collision_intent: 'intentional', points: [{ x: 90, y: 10 }, { x: 10, y: 40 }] }]);
    expect(result[0]).toMatchObject({ intentional: true });
    expect(result[0].explanation).toContain('intentional crossing');
  });
});
