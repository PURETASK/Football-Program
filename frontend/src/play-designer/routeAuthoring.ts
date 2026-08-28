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
