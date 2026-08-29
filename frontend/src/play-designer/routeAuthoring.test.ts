import { describe, expect, it } from 'vitest';
import { routeAuthoringPatch, routeBranchGeometryPatch, routeBranchPointRemovalPatch, routeConstructionPatch, routeGeometryPatch, routePointRemovalPatch } from './routeAuthoring';

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

  it('keeps direct stem and break edits synchronized with the route contract', () => {
    const element = {
      id: 'R1', kind: 'route', route_family: 'dropback', break_type: 'dig',
      stem_depth_yards: 8, break_depth_yards: 12,
      points: [{ x: 20, y: 32 }, { x: 20, y: 24 }, { x: 20, y: 20 }, { x: 28, y: 12 }],
    };
    const stem = routeGeometryPatch(element, { id: 'D1', unit: 'offense' }, [...element.points.slice(0, 1), { x: 24, y: 22 }, ...element.points.slice(2)], 1);
    expect(stem).toMatchObject({ stem_depth_yards: 10, phase: 'route' });
    const breakPatch = routeGeometryPatch(element, { id: 'D1', unit: 'offense' }, [...element.points.slice(0, 2), { x: 22, y: 18 }, ...element.points.slice(3)], 2);
    expect(breakPatch).toMatchObject({ break_depth_yards: 14, phase: 'route' });
    expect(breakPatch.points).toHaveLength(4);
  });

  it('keeps alternate-path handle edits synchronized with the branch contract', () => {
    const element = {
      id: 'R1', kind: 'route', route_family: 'dropback', break_type: 'dig',
      points: [{ x: 20, y: 32 }, { x: 20, y: 20 }],
      branches: [{ id: 'R1-OPT', label: 'Alert', condition: 'If leverage changes', points: [{ x: 20, y: 20 }, { x: 30, y: 14 }, { x: 42, y: 14 }] }],
    };
    const patch = routeBranchGeometryPatch(element, { id: 'D1', unit: 'offense' }, 'R1-OPT', [{ x: 20, y: 20 }, { x: 30, y: 18 }, { x: 42, y: 14 }], 1);
    expect(patch).toMatchObject({ phase: 'route', branches: [expect.objectContaining({ id: 'R1-OPT', break_depth_yards: 2, route_family: 'dropback', break_type: 'dig' })] });
    expect(patch.branches?.[0].points).toEqual([{ x: 20, y: 20 }, { x: 30, y: 18 }, { x: 42, y: 14 }]);
  });

  it('removes a primary handle while recomputing remaining stem and break depths', () => {
    const element = {
      id: 'R1', kind: 'route', route_family: 'dropback', break_type: 'dig',
      stem_depth_yards: 8, break_depth_yards: 12,
      points: [{ x: 20, y: 32 }, { x: 22, y: 24 }, { x: 28, y: 18 }, { x: 34, y: 12 }, { x: 40, y: 8 }],
    };
    expect(routePointRemovalPatch(element, { id: 'D1', unit: 'offense' }, 1)).toMatchObject({
      phase: 'route', stem_depth_yards: 14, break_depth_yards: 20,
      points: [{ x: 20, y: 32 }, { x: 28, y: 18 }, { x: 34, y: 12 }, { x: 40, y: 8 }],
    });
  });

  it('removes an alternate-path handle while preserving inherited route semantics', () => {
    const element = {
      id: 'R1', kind: 'route', route_family: 'dropback', break_type: 'dig',
      points: [{ x: 20, y: 32 }, { x: 20, y: 20 }],
      branches: [{ id: 'R1-OPT', label: 'Alert', condition: 'If leverage changes', points: [{ x: 20, y: 20 }, { x: 28, y: 16 }, { x: 34, y: 12 }, { x: 42, y: 12 }] }],
    };
    expect(routeBranchPointRemovalPatch(element, { id: 'D1', unit: 'offense' }, 'R1-OPT', 1)).toMatchObject({
      phase: 'route', branches: [expect.objectContaining({ route_family: 'dropback', break_type: 'dig', stem_depth_yards: 8, break_depth_yards: 8, points: [{ x: 20, y: 20 }, { x: 34, y: 12 }, { x: 42, y: 12 }] })],
    });
  });
});
