import type { PlayElement } from '../types';
import { anglePatch, collisionIds, depthPatch, elementProgress, fieldRect, handleRole, insertPointOnNearestSegment, landmarkPatch, normalizePoint, pathIntersectsRect, positionAlongPath, routeCollisions, simplifyPath, smoothPathData } from './geometry';

describe('play designer geometry', () => {
  it('clamps field coordinates and applies the authoring grid', () => {
    expect(normalizePoint({ x: 100.7, y: -2 }, true)).toEqual({ x: 100, y: 0 });
    expect(normalizePoint({ x: 42.36, y: 19.94 }, false)).toEqual({ x: 42.4, y: 19.9 });
  });

  it('simplifies noisy pointer input while retaining the coached break', () => {
    const points = [{ x: 10, y: 30 }, { x: 11, y: 29.9 }, { x: 20, y: 20 }, { x: 29, y: 10.1 }, { x: 30, y: 10 }, { x: 46, y: 10 }];
    const result = simplifyPath(points, 0.5);
    expect(result.length).toBeLessThan(points.length);
    expect(result[0]).toEqual({ x: 10, y: 30 });
    expect(result.at(-1)).toEqual({ x: 46, y: 10 });
    expect(smoothPathData(result)).toMatch(/^M 10 30/);
  });

  it('interpolates movement by actual path distance', () => {
    expect(positionAlongPath([{ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 10, y: 30 }], 0.5)).toEqual({ x: 10, y: 10 });
  });

  it('uses per-assignment timing windows for playback', () => {
    const element: PlayElement = { id: 'R1', kind: 'route', start_ms: 500, end_ms: 2500 };
    expect(elementProgress(element, 0, 3000)).toBe(0);
    expect(elementProgress(element, 1500, 3000)).toBe(0.5);
    expect(elementProgress(element, 3000, 3000)).toBe(1);
  });

  it('maps playback progress through authored phases for visible route teaching', () => {
    const element: PlayElement = { id: 'PHASED', kind: 'route', start_ms: 0, end_ms: 2000, timing: { start_ms: 0, end_ms: 2000, phases: [
      { id: 'release', start_ms: 0, end_ms: 300 },
      { id: 'stem', start_ms: 300, end_ms: 1400 },
      { id: 'break', start_ms: 1400, end_ms: 1700 },
      { id: 'finish', start_ms: 1700, end_ms: 2000 },
    ] } };
    expect(elementProgress(element, 300, 2000)).toBeCloseTo(0.25);
    expect(elementProgress(element, 1400, 2000)).toBeCloseTo(0.5);
    expect(elementProgress(element, 1550, 2000)).toBeCloseTo(0.625);
  });

  it('detects paths that cross a marquee even when their handles sit outside it', () => {
    const rect = fieldRect({ x: 20, y: 20 }, { x: 30, y: 30 });
    expect(pathIntersectsRect([{ x: 10, y: 25 }, { x: 40, y: 25 }], rect)).toBe(true);
    expect(pathIntersectsRect([{ x: 10, y: 10 }, { x: 40, y: 10 }], rect)).toBe(false);
  });

  it('inserts a snapped handle on the nearest path segment', () => {
    const result = insertPointOnNearestSegment([{ x: 10, y: 30 }, { x: 30, y: 10 }, { x: 50, y: 10 }], { x: 41, y: 13 }, true);
    expect(result.index).toBe(2);
    expect(result.points).toEqual([{ x: 10, y: 30 }, { x: 30, y: 10 }, { x: 41, y: 10 }, { x: 50, y: 10 }]);
  });

  it('moves a route endpoint to the requested depth while preserving its start', () => {
    const design = { id: 'DEPTH', unit: 'offense', field_context: { line_of_scrimmage_y: 26.5 } };
    const element: PlayElement = { id: 'ROUTE', kind: 'route', points: [{ x: 12, y: 32 }, { x: 22, y: 18 }] };
    expect(depthPatch(element, design, 12)).toMatchObject({ depth_yards: 12, points: [{ x: 12, y: 32 }, { x: 22, y: 20 }] });
  });

  it('snaps an endpoint to a field landmark and stores its readable label', () => {
    const design = { id: 'LANDMARK', unit: 'offense', field_context: { line_of_scrimmage_y: 26.5 } };
    const element: PlayElement = { id: 'ROUTE', kind: 'route', points: [{ x: 12, y: 32 }, { x: 22, y: 18 }] };
    expect(landmarkPatch(element, design, 'right_hash')).toMatchObject({ landmark: 'Right hash', points: [{ x: 12, y: 32 }, { x: 62, y: 18 }] });
  });

  it('moves the final handle with a unit-aware angle preset and names semantic handles', () => {
    const design = { id: 'ANGLE', unit: 'offense' };
    const element: PlayElement = { id: 'ROUTE', kind: 'route', points: [{ x: 10, y: 32 }, { x: 20, y: 22 }, { x: 30, y: 10 }] };
    const angled = anglePatch(element, design, 'inside');
    expect(angled.angle_preset).toBe('inside');
    expect(angled.points?.[0]).toEqual({ x: 10, y: 32 });
    expect(angled.points?.at(-1)?.y).toBeLessThan(10);
    expect(handleRole(element, 0)).toBe('start');
    expect(handleRole(element, 1)).toBe('break');
    expect(handleRole(element, 2)).toBe('finish');
  });

  it('flags only timed intersecting route pairs for canvas collision feedback', () => {
    const make = (id: string, points: [{ x: number; y: number }, { x: number; y: number }], start_ms = 0, end_ms = 1000): PlayElement => ({ id, kind: 'route', points, start_ms, end_ms });
    expect(collisionIds([make('A', [{ x: 10, y: 30 }, { x: 40, y: 10 }]), make('B', [{ x: 10, y: 10 }, { x: 40, y: 30 }])])).toEqual(new Set(['A', 'B']));
    expect(collisionIds([make('A', [{ x: 10, y: 30 }, { x: 40, y: 10 }]), make('B', [{ x: 10, y: 10 }, { x: 40, y: 30 }], 1001, 2000)])).toEqual(new Set());
  });

  it('flags near-miss routes when their teaching corridors overlap', () => {
    const result = routeCollisions([
      { id: 'A', kind: 'route', points: [{ x: 10, y: 20 }, { x: 90, y: 20 }], start_ms: 500, end_ms: 1500 },
      { id: 'B', kind: 'route', points: [{ x: 10, y: 21 }, { x: 90, y: 21 }], start_ms: 1000, end_ms: 2000 },
    ]);
    expect(result[0]).toMatchObject({ kind: 'corridor', minimumSeparation: 1, overlapStartMs: 1000, overlapEndMs: 1500 });
    expect(result[0].explanation).toContain('corridors');
  });
});
