import { describe, expect, it } from 'vitest';
import { routeAuthoringPatch, routeConstructionPatch } from './routeAuthoring';

describe('route construction authoring', () => {
  it('stores stem, break, finish, and option semantics in the route phase', () => {
    expect(routeAuthoringPatch({ route_family: 'dropback', stem_depth_yards: 12, break_type: 'dig', break_depth_yards: 12, finish_direction: 'inside', option_rule: 'leverage' })).toMatchObject({ route_family: 'dropback', stem_depth_yards: 12, break_type: 'dig', break_depth_yards: 12, finish_direction: 'inside', option_rule: 'leverage', phase: 'route' });
  });

  it('keeps stem, break, and finish controls synchronized with polyline geometry', () => {
    const element = { id: 'R1', kind: 'route', points: [{ x: 20, y: 32 }, { x: 20, y: 24 }, { x: 20, y: 12 }] };
    const patch = routeConstructionPatch(element, { id: 'D1', unit: 'offense' }, { stem_depth_yards: 8, break_depth_yards: 12, finish_direction: 'inside' });
    expect(patch).toMatchObject({ phase: 'route', stem_depth_yards: 8, break_depth_yards: 12, finish_direction: 'inside' });
    expect(patch.points).toHaveLength(4);
    expect(patch.points?.[1]).toEqual({ x: 20, y: 24 });
    expect(patch.points?.[2]).toEqual({ x: 20, y: 20 });
    expect(patch.points?.[3]).toEqual({ x: 24, y: 12 });
  });

  it('materializes common break selections into editable football geometry', () => {
    const element = { id: 'R1', kind: 'route', points: [{ x: 20, y: 30 }, { x: 20, y: 20 }, { x: 20, y: 20 }] };
    const patch = routeConstructionPatch(element, { id: 'D1', unit: 'offense' }, { break_type: 'speed_out' });
    expect(patch).toMatchObject({ phase: 'route', break_type: 'speed_out' });
    expect(patch.points?.at(-1)).toEqual({ x: 11, y: 20 });
  });
});
