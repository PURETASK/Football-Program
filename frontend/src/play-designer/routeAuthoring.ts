import type { PlayDesign, PlayElement, Point } from '../types';
import { clamp, elementPoints, normalizePoint } from './geometry';

export const ROUTE_FAMILIES = [
  ['quick', 'Quick game'], ['dropback', 'Dropback'], ['intermediate', 'Intermediate'], ['vertical', 'Vertical'],
  ['screen', 'Screen'], ['crossing', 'Crossing'], ['sight', 'Sight-adjust'],
] as const;

export const ROUTE_BREAKS = [
  ['none', 'No break'], ['speed_out', 'Speed out'], ['comeback', 'Comeback'], ['curl', 'Curl'],
  ['dig', 'Dig / in'], ['over', 'Over / deep cross'], ['post', 'Post'], ['corner', 'Corner'],
  ['whip', 'Whip / pivot'], ['choice', 'Choice break'], ['option', 'Option break'],
] as const;

export const ROUTE_FINISHES = [
  ['vertical', 'Finish vertical'], ['inside', 'Finish inside'], ['outside', 'Finish outside'],
  ['settle', 'Settle in window'], ['runaway', 'Run away from leverage'],
] as const;

export const ROUTE_OPTION_RULES = [
  ['none', 'No option'], ['leverage', 'Convert by leverage'], ['safety', 'Convert by safety rotation'],
  ['coverage', 'Convert by coverage'], ['sight', 'Sight-adjust on pressure'],
] as const;

export function routeAuthoringPatch(patch: Partial<PlayElement>): Partial<PlayElement> {
  return { ...patch, phase: 'route' };
}

function depthY(start: Point, design: PlayDesign, depth: number): number {
  const direction = design.unit === 'defense' ? 1 : -1;
  return clamp(start.y + direction * depth, 0, 53);
}

/**
 * Apply route semantics and keep the editable polyline in sync with them.
 * The canvas remains the source of exact lateral geometry, while these
 * controls provide a deterministic coach-facing stem/break/finish contract.
 */
export function routeConstructionPatch(element: PlayElement, design: PlayDesign, patch: Partial<PlayElement>): Partial<PlayElement> {
  const next: Partial<PlayElement> = routeAuthoringPatch(patch);
  const points = elementPoints(element);
  if (points.length < 2) return next;
  const nextPoints = points.map((point) => ({ ...point }));
  const start = nextPoints[0];
  const stemDepth = Number(patch.stem_depth_yards);
  if (patch.stem_depth_yards !== undefined && Number.isFinite(stemDepth) && stemDepth >= 0) {
    if (nextPoints.length === 3) {
      const previousBreak = nextPoints[1];
      nextPoints.splice(1, 0, { x: (start.x + previousBreak.x) / 2, y: (start.y + previousBreak.y) / 2 });
    }
    const stemIndex = nextPoints.length >= 3 ? 1 : nextPoints.length - 1;
    nextPoints[stemIndex].y = depthY(start, design, stemDepth);
    nextPoints[stemIndex] = normalizePoint(nextPoints[stemIndex], false);
  }
  const breakDepth = Number(patch.break_depth_yards);
  if (patch.break_depth_yards !== undefined && Number.isFinite(breakDepth) && breakDepth >= 0) {
    const breakIndex = nextPoints.length >= 3 ? nextPoints.length - 2 : nextPoints.length - 1;
    nextPoints[breakIndex].y = depthY(start, design, breakDepth);
    nextPoints[breakIndex] = normalizePoint(nextPoints[breakIndex], false);
  }
  if (patch.break_type && nextPoints.length >= 2) {
    const breakIndex = nextPoints.length >= 3 ? nextPoints.length - 2 : nextPoints.length - 1;
    const breakPoint = nextPoints[breakIndex];
    const finish = nextPoints[nextPoints.length - 1];
    const outside = start.x <= 50 ? -1 : 1;
    const inside = -outside;
    const breakType = patch.break_type;
    const lateral = (amount: number) => { finish.x = clamp(breakPoint.x + amount, 0, 100); };
    if (breakType === 'speed_out') lateral(outside * 9);
    if (breakType === 'dig' || breakType === 'over') lateral(inside * (breakType === 'over' ? 12 : 9));
    if (breakType === 'post') lateral(inside * 7);
    if (breakType === 'corner') lateral(outside * 7);
    if (breakType === 'comeback' || breakType === 'curl') {
      lateral(outside * 2);
      finish.y = clamp(breakPoint.y + (design.unit === 'defense' ? -4 : 4), 0, 53);
    }
    if (breakType === 'whip') {
      lateral(outside * 6);
      finish.y = clamp(breakPoint.y + (design.unit === 'defense' ? 2 : -2), 0, 53);
    }
    nextPoints[breakIndex] = normalizePoint(breakPoint, false);
    nextPoints[nextPoints.length - 1] = normalizePoint(finish, false);
  }
  if (patch.finish_direction && nextPoints.length >= 2) {
    const finish = nextPoints[nextPoints.length - 1];
    const direction = patch.finish_direction === 'inside' ? (start.x <= 50 ? 1 : -1)
      : patch.finish_direction === 'outside' ? (start.x <= 50 ? -1 : 1)
        : patch.finish_direction === 'vertical' ? 0 : 1;
    if (direction) finish.x = clamp(finish.x + direction * 4, 0, 100);
    nextPoints[nextPoints.length - 1] = normalizePoint(finish, false);
  }
  if (element.points) next.points = nextPoints;
  else next.path = nextPoints;
  return next;
}

/**
 * Persist a direct drag of a route's semantic points.  A route is more useful
 * to a coach when its visual geometry and its coaching contract cannot drift
 * apart: moving the stem or break point updates the corresponding depth in
 * yards while preserving all other element metadata.
 *
 * We intentionally only emit semantic fields for routes that already carry a
 * route contract.  This keeps legacy/freehand paths compatible with the
 * generic editor payload while allowing catalog-created routes to remain
 * explainable after direct manipulation.
 */
export function routeGeometryPatch(
  element: PlayElement,
  design: PlayDesign,
  points: Point[],
  pointIndex: number,
): Partial<PlayElement> {
  const patch: Partial<PlayElement> = element.points ? { points } : { path: points };
  if (element.kind !== 'route' || points.length < 2) return patch;
  const hasContract = [
    element.route_family,
    element.stem_depth_yards,
    element.break_type,
    element.break_depth_yards,
    element.finish_direction,
    element.option_rule,
  ].some((value) => value !== undefined);
  if (!hasContract) return patch;
  const start = points[0];
  const depth = Math.abs(points[pointIndex].y - start.y);
  if (pointIndex > 0 && pointIndex < points.length - 1) {
    if (pointIndex === points.length - 2) patch.break_depth_yards = Math.round(depth * 10) / 10;
    else patch.stem_depth_yards = Math.round(depth * 10) / 10;
  }
  // Keep the semantic phase explicit so downstream validators and exports
  // continue to treat a manually adjusted route as a route assignment.
  patch.phase = 'route';
  // Referencing design here makes the direction rule visible at the call site
  // and protects this helper if field orientation becomes configurable.
  void design;
  return patch;
}
