import type { PlayDesign, PlayElement, Point } from '../types';

export const FIELD_WIDTH = 100;
export const FIELD_HEIGHT = 53;

export interface FieldRect {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function normalizePoint(point: Point, snap = true): Point {
  const precision = snap ? 1 : 10;
  return {
    x: Math.round(clamp(point.x, 0, FIELD_WIDTH) * precision) / precision,
    y: Math.round(clamp(point.y, 0, FIELD_HEIGHT) * precision) / precision,
  };
}

export function translatePoints(points: Point[], delta: Point, snap = true): Point[] {
  return points.map((point) => normalizePoint({ x: point.x + delta.x, y: point.y + delta.y }, snap));
}

export function fieldRect(start: Point, end: Point): FieldRect {
  return {
    left: Math.min(start.x, end.x),
    right: Math.max(start.x, end.x),
    top: Math.min(start.y, end.y),
    bottom: Math.max(start.y, end.y),
  };
}

export function pointInRect(point: Point, rect: FieldRect): boolean {
  return point.x >= rect.left && point.x <= rect.right && point.y >= rect.top && point.y <= rect.bottom;
}

function segmentIntersectsRect(start: Point, end: Point, rect: FieldRect): boolean {
  if (pointInRect(start, rect) || pointInRect(end, rect)) return true;
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  let minimum = 0;
  let maximum = 1;
  const boundaries: Array<[number, number]> = [
    [-dx, start.x - rect.left],
    [dx, rect.right - start.x],
    [-dy, start.y - rect.top],
    [dy, rect.bottom - start.y],
  ];
  for (const [direction, distance] of boundaries) {
    if (direction === 0) {
      if (distance < 0) return false;
      continue;
    }
    const ratio = distance / direction;
    if (direction < 0) minimum = Math.max(minimum, ratio);
    else maximum = Math.min(maximum, ratio);
    if (minimum > maximum) return false;
  }
  return true;
}

export function pathIntersectsRect(points: Point[], rect: FieldRect): boolean {
  if (points.some((point) => pointInRect(point, rect))) return true;
  return points.slice(1).some((point, index) => segmentIntersectsRect(points[index], point, rect));
}

export function pointerToFieldPoint(
  clientX: number,
  clientY: number,
  bounds: Pick<DOMRect, 'left' | 'top' | 'width' | 'height'>,
  snap = true,
): Point {
  return normalizePoint(
    {
      x: ((clientX - bounds.left) / bounds.width) * FIELD_WIDTH,
      y: ((clientY - bounds.top) / bounds.height) * FIELD_HEIGHT,
    },
    snap,
  );
}

export function pointDistance(a: Point, b: Point): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

function perpendicularDistance(point: Point, start: Point, end: Point): number {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  if (dx === 0 && dy === 0) return pointDistance(point, start);
  const ratio = ((point.x - start.x) * dx + (point.y - start.y) * dy) / (dx * dx + dy * dy);
  const projection = { x: start.x + ratio * dx, y: start.y + ratio * dy };
  return pointDistance(point, projection);
}

export function simplifyPath(points: Point[], tolerance = 0.7): Point[] {
  if (points.length <= 2) return points.map((point) => normalizePoint(point, false));
  let maxDistance = 0;
  let splitIndex = 0;
  for (let index = 1; index < points.length - 1; index += 1) {
    const distance = perpendicularDistance(points[index], points[0], points[points.length - 1]);
    if (distance > maxDistance) {
      maxDistance = distance;
      splitIndex = index;
    }
  }
  if (maxDistance <= tolerance) return [normalizePoint(points[0], false), normalizePoint(points[points.length - 1], false)];
  const left = simplifyPath(points.slice(0, splitIndex + 1), tolerance);
  const right = simplifyPath(points.slice(splitIndex), tolerance);
  return [...left.slice(0, -1), ...right];
}

export function insertPointOnNearestSegment(points: Point[], candidate: Point, snap = true): { points: Point[]; index: number } {
  if (points.length < 2) return { points: [...points, normalizePoint(candidate, snap)], index: points.length };
  let nearest = normalizePoint(candidate, snap);
  let nearestDistance = Number.POSITIVE_INFINITY;
  let insertIndex = 1;
  for (let index = 0; index < points.length - 1; index += 1) {
    const start = points[index];
    const end = points[index + 1];
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const denominator = dx * dx + dy * dy;
    const ratio = denominator
      ? clamp(((candidate.x - start.x) * dx + (candidate.y - start.y) * dy) / denominator, 0, 1)
      : 0;
    const projected = normalizePoint({ x: start.x + ratio * dx, y: start.y + ratio * dy }, snap);
    const distance = pointDistance(projected, candidate);
    if (distance < nearestDistance) {
      nearest = projected;
      nearestDistance = distance;
      insertIndex = index + 1;
    }
  }
  return { points: [...points.slice(0, insertIndex), nearest, ...points.slice(insertIndex)], index: insertIndex };
}

export function smoothPathData(points: Point[]): string {
  if (!points.length) return '';
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  if (points.length === 2) return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
  const commands = [`M ${points[0].x} ${points[0].y}`];
  for (let index = 1; index < points.length - 1; index += 1) {
    const next = points[index + 1];
    const midpoint = { x: (points[index].x + next.x) / 2, y: (points[index].y + next.y) / 2 };
    commands.push(`Q ${points[index].x} ${points[index].y} ${midpoint.x} ${midpoint.y}`);
  }
  const last = points[points.length - 1];
  commands.push(`L ${last.x} ${last.y}`);
  return commands.join(' ');
}

export function polylinePathData(points: Point[]): string {
  if (!points.length) return '';
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
}

export const ANGLE_PRESETS = [
  ['vertical', 'Vertical'],
  ['inside', 'Break inside'],
  ['outside', 'Break outside'],
  ['flat_left', 'Flat left'],
  ['flat_right', 'Flat right'],
  ['diagonal_in', 'Diagonal inside'],
  ['diagonal_out', 'Diagonal outside'],
] as const;

export function handleRole(element: PlayElement, index: number): 'start' | 'stem' | 'break' | 'finish' {
  const count = elementPoints(element).length;
  if (index === 0) return 'start';
  if (index === count - 1) return 'finish';
  return index === count - 2 ? 'break' : 'stem';
}

export function anglePatch(element: PlayElement, design: PlayDesign, preset: string): Partial<PlayElement> {
  const points = elementPoints(element);
  if (points.length < 2) return { angle_preset: preset };
  const first = points[0];
  const last = points.at(-1)!;
  const distance = Math.max(2, pointDistance(first, last));
  const inward = first.x <= 50 ? 1 : -1;
  const outward = inward * -1;
  const vertical = design.unit === 'defense' ? 1 : -1;
  const vectors: Record<string, Point> = {
    vertical: { x: 0, y: vertical },
    inside: { x: inward * 0.55, y: vertical * 0.84 },
    outside: { x: outward * 0.55, y: vertical * 0.84 },
    flat_left: { x: -1, y: 0 },
    flat_right: { x: 1, y: 0 },
    diagonal_in: { x: inward * 0.78, y: vertical * 0.62 },
    diagonal_out: { x: outward * 0.78, y: vertical * 0.62 },
  };
  const vector = vectors[preset] ?? vectors.vertical;
  const length = Math.hypot(vector.x, vector.y) || 1;
  const endpoint = { x: clamp(first.x + (vector.x / length) * distance, 1, 99), y: clamp(first.y + (vector.y / length) * distance, 1, 52) };
  return { angle_preset: preset, ...setLastPoint(element, endpoint) };
}

function segmentsIntersect(first: Point, second: Point, third: Point, fourth: Point): boolean {
  const orientation = (a: Point, b: Point, c: Point) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
  const onSegment = (a: Point, b: Point, c: Point) => Math.min(a.x, c.x) - 0.01 <= b.x && b.x <= Math.max(a.x, c.x) + 0.01 && Math.min(a.y, c.y) - 0.01 <= b.y && b.y <= Math.max(a.y, c.y) + 0.01;
  const a = orientation(first, second, third);
  const b = orientation(first, second, fourth);
  const c = orientation(third, fourth, first);
  const d = orientation(third, fourth, second);
  if (((a > 0 && b < 0) || (a < 0 && b > 0)) && ((c > 0 && d < 0) || (c < 0 && d > 0))) return true;
  return (Math.abs(a) < 0.01 && onSegment(first, third, second)) || (Math.abs(b) < 0.01 && onSegment(first, fourth, second)) || (Math.abs(c) < 0.01 && onSegment(third, first, fourth)) || (Math.abs(d) < 0.01 && onSegment(third, second, fourth));
}

function pointSegmentDistance(point: Point, start: Point, end: Point): number {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const denominator = dx * dx + dy * dy;
  if (!denominator) return pointDistance(point, start);
  const ratio = clamp(((point.x - start.x) * dx + (point.y - start.y) * dy) / denominator, 0, 1);
  return pointDistance(point, { x: start.x + ratio * dx, y: start.y + ratio * dy });
}

function segmentDistance(first: Point, second: Point, third: Point, fourth: Point): number {
  if (segmentsIntersect(first, second, third, fourth)) return 0;
  return Math.min(
    pointSegmentDistance(first, third, fourth),
    pointSegmentDistance(second, third, fourth),
    pointSegmentDistance(third, first, second),
    pointSegmentDistance(fourth, first, second),
  );
}

function pathDistance(first: Point[], second: Point[]): number {
  let minimum = Number.POSITIVE_INFINITY;
  for (let firstIndex = 1; firstIndex < first.length; firstIndex += 1) {
    for (let secondIndex = 1; secondIndex < second.length; secondIndex += 1) {
      minimum = Math.min(minimum, segmentDistance(first[firstIndex - 1], first[firstIndex], second[secondIndex - 1], second[secondIndex]));
    }
  }
  return minimum;
}

export function pathsIntersect(first: Point[], second: Point[]): boolean {
  for (let firstIndex = 1; firstIndex < first.length; firstIndex += 1) {
    for (let secondIndex = 1; secondIndex < second.length; secondIndex += 1) {
      if (segmentsIntersect(first[firstIndex - 1], first[firstIndex], second[secondIndex - 1], second[secondIndex])) return true;
    }
  }
  return false;
}

function timingOverlap(first: PlayElement, second: PlayElement): { start: number; end: number } | undefined {
  const firstStart = Number(first.start_ms ?? first.timing?.start_ms ?? 0);
  const firstEnd = Number(first.end_ms ?? first.timing?.end_ms ?? 999999);
  const secondStart = Number(second.start_ms ?? second.timing?.start_ms ?? 0);
  const secondEnd = Number(second.end_ms ?? second.timing?.end_ms ?? 999999);
  const start = Math.max(firstStart, secondStart);
  const end = Math.min(firstEnd, secondEnd);
  return start <= end ? { start, end } : undefined;
}

export function collisionIds(elements: PlayElement[]): Set<string> {
  const collisions = new Set<string>();
  for (const collision of routeCollisions(elements)) {
    collisions.add(collision.firstId);
    collisions.add(collision.secondId);
  }
  return collisions;
}

export interface RouteCollision {
  firstId: string;
  secondId: string;
  intentional: boolean;
  explanation: string;
  minimumSeparation: number;
  corridorThreshold: number;
  kind: 'intersection' | 'corridor';
  overlapStartMs: number;
  overlapEndMs: number;
}

function routeCorridor(element: PlayElement): number {
  const configured = Number(element.collision_corridor_yards);
  return Number.isFinite(configured) && configured > 0 ? configured : 1.5;
}

export function routeCollisions(elements: PlayElement[]): RouteCollision[] {
  const routes = elements.filter((element) => element.kind === 'route' && !element.hidden && elementPoints(element).length > 1);
  const collisions: RouteCollision[] = [];
  for (let index = 0; index < routes.length; index += 1) {
    for (let secondIndex = index + 1; secondIndex < routes.length; secondIndex += 1) {
      const first = routes[index]; const second = routes[secondIndex];
      const overlap = timingOverlap(first, second);
      if (!overlap) continue;
      const minimumSeparation = pathDistance(elementPoints(first), elementPoints(second));
      const corridorThreshold = Math.max(routeCorridor(first), routeCorridor(second));
      if (minimumSeparation > corridorThreshold) continue;
      const intentional = first.collision_intent === 'intentional' && second.collision_intent === 'intentional';
      const kind = minimumSeparation === 0 ? 'intersection' : 'corridor';
      const separation = minimumSeparation.toFixed(1);
      const overlapWindow = `${(overlap.start / 1000).toFixed(2)}–${(overlap.end / 1000).toFixed(2)}s`;
      collisions.push({ firstId: first.id, secondId: second.id, intentional, minimumSeparation, corridorThreshold, kind, overlapStartMs: overlap.start, overlapEndMs: overlap.end, explanation: intentional
        ? `Both routes are marked as an intentional crossing during ${overlapWindow}; minimum separation is ${separation} yd. Confirm spacing and timing in the teaching view.`
        : kind === 'intersection'
          ? `Routes intersect during ${overlapWindow}; separate the corridor or explicitly document the intentional crossing.`
          : `Route corridors come within ${separation} yd during ${overlapWindow}; maintain at least ${corridorThreshold.toFixed(1)} yd or document the intentional crossing.` });
    }
  }
  return collisions;
}

export const LANDMARK_SNAP_OPTIONS = [
  ['left_hash', 'Left hash'],
  ['middle_hash', 'Middle hash'],
  ['right_hash', 'Right hash'],
  ['line_of_scrimmage', 'Line of scrimmage'],
  ['five_yards', 'Five-yard landmark'],
  ['ten_yards', 'Ten-yard landmark'],
  ['fifteen_yards', 'Fifteen-yard landmark'],
  ['goal_line', 'Goal line'],
] as const;

function setLastPoint(element: PlayElement, point: Point): Partial<PlayElement> {
  const points = elementPoints(element);
  if (!points.length) return {};
  const nextPoints = [...points.slice(0, -1), normalizePoint(point, false)];
  return element.points ? { points: nextPoints } : { path: nextPoints };
}

export function depthPatch(element: PlayElement, design: PlayDesign, depth: number | undefined): Partial<PlayElement> {
  if (depth === undefined || !Number.isFinite(depth)) return { depth_yards: undefined };
  const points = elementPoints(element);
  if (!points.length) return { depth_yards: depth };
  const first = points[0];
  const nextY = design.unit === 'defense' ? first.y + depth : first.y - depth;
  return { depth_yards: depth, ...setLastPoint(element, { ...points.at(-1)!, y: clamp(nextY, 1, FIELD_HEIGHT) }) };
}

export function landmarkPatch(element: PlayElement, design: PlayDesign, landmarkId: string): Partial<PlayElement> {
  const points = elementPoints(element);
  if (!points.length) return {};
  const last = points.at(-1)!;
  const lineOfScrimmage = Number(design.field_context?.line_of_scrimmage_y ?? 26.5);
  const label = LANDMARK_SNAP_OPTIONS.find(([value]) => value === landmarkId)?.[1] ?? landmarkId;
  const next = { ...last };
  if (landmarkId === 'left_hash') next.x = 38;
  if (landmarkId === 'middle_hash') next.x = 50;
  if (landmarkId === 'right_hash') next.x = 62;
  if (landmarkId === 'line_of_scrimmage') next.y = lineOfScrimmage;
  if (landmarkId === 'five_yards') next.y = lineOfScrimmage + (design.unit === 'defense' ? 5 : -5);
  if (landmarkId === 'ten_yards') next.y = lineOfScrimmage + (design.unit === 'defense' ? 10 : -10);
  if (landmarkId === 'fifteen_yards') next.y = lineOfScrimmage + (design.unit === 'defense' ? 15 : -15);
  if (landmarkId === 'goal_line') next.y = design.unit === 'defense' ? FIELD_HEIGHT : 1;
  return { landmark: label, ...setLastPoint(element, { x: clamp(next.x, 1, 99), y: clamp(next.y, 1, 52) }) };
}

export function positionAlongPath(points: Point[], progress: number): Point | null {
  if (!points.length) return null;
  if (points.length === 1) return points[0];
  const lengths = points.slice(1).map((point, index) => pointDistance(points[index], point));
  const total = lengths.reduce((sum, length) => sum + length, 0);
  if (!total) return points[0];
  let remaining = clamp(progress, 0, 1) * total;
  for (let index = 0; index < lengths.length; index += 1) {
    if (remaining <= lengths[index]) {
      const ratio = lengths[index] ? remaining / lengths[index] : 0;
      return {
        x: points[index].x + (points[index + 1].x - points[index].x) * ratio,
        y: points[index].y + (points[index + 1].y - points[index].y) * ratio,
      };
    }
    remaining -= lengths[index];
  }
  return points[points.length - 1];
}

export function elementPoints(element: PlayElement): Point[] {
  return element.points ?? element.path ?? [];
}

export function elementProgress(element: PlayElement, timeMs: number, durationMs: number): number {
  const start = Number(element.start_ms ?? element.timing?.start_ms ?? 0);
  const end = Number(element.end_ms ?? element.timing?.end_ms ?? durationMs);
  if (timeMs <= start) return 0;
  if (timeMs >= end) return 1;
  const phases = element.timing?.phases?.filter((phase) => Number.isFinite(phase.start_ms) && Number.isFinite(phase.end_ms) && phase.end_ms > phase.start_ms);
  if (phases?.length) {
    const phaseIndex = phases.findIndex((phase) => timeMs >= phase.start_ms && timeMs <= phase.end_ms);
    if (phaseIndex >= 0) {
      const phase = phases[phaseIndex];
      const phaseProgress = (timeMs - phase.start_ms) / Math.max(1, phase.end_ms - phase.start_ms);
      return clamp((phaseIndex + clamp(phaseProgress, 0, 1)) / phases.length, 0, 1);
    }
  }
  return (timeMs - start) / Math.max(1, end - start);
}

export function mirrorPoints(points: Point[]): Point[] {
  return points.map((point) => ({ x: FIELD_WIDTH - point.x, y: point.y }));
}
