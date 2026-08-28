import type { PlayAsset, PlayDesign, PlayElement, PlayPlayer, Point } from '../types';
import { defaultTimelinePhases } from './timelineModel';

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function directionSign(design: PlayDesign): number {
  return design.field_context?.direction === 'left' ? -1 : 1;
}

function boundedPoints(points: Point[]): Point[] {
  return points.map((point) => ({ x: clamp(Number(point.x), 1, 99), y: clamp(Number(point.y), 1, 52) }));
}

function token(asset: PlayAsset): string {
  return [asset.term, asset.display_name, ...(asset.aliases ?? [])].filter(Boolean).join(' ').toLowerCase();
}

function offensivePath(start: Point, asset: PlayAsset, sign: number): Point[] {
  const term = token(asset);
  const x = start.x;
  const stem = 6;
  if (asset.kind === 'motion' || term.includes('motion')) {
    const distance = term.includes('orbit') ? 15 : term.includes('zip') ? 9 : 20;
    const bend = term.includes('orbit') ? [{ x: x + sign * 4, y: start.y + 3 }] : [];
    return boundedPoints([start, ...bend, { x: x + sign * distance, y: start.y }]);
  }
  if (asset.kind === 'run' || term.includes('zone') || term.includes('power') || term.includes('counter')) {
    const aimingPoint = term.includes('outside') ? x + sign * 7 : term.includes('wide') ? x + sign * 11 : 50;
    return boundedPoints([start, { x: aimingPoint, y: start.y - 3 }, { x: aimingPoint + sign * 2, y: start.y - 10 }]);
  }
  if (asset.kind === 'block' || asset.kind === 'protection') return boundedPoints([start, { x: x + sign * 2.5, y: start.y - 1.5 }, { x: x + sign * 4.5, y: start.y - 3 }]);
  if (term.includes('screen')) return boundedPoints([start, { x: x + sign * 2, y: start.y - 1 }, { x: x + sign * 8, y: start.y - 1 }, { x: x + sign * 11, y: start.y - 5 }]);
  if (term.includes('flat') || term.includes('swing') || term.includes('arrow')) return boundedPoints([start, { x: x + sign * 4, y: start.y - 2 }, { x: x + sign * 10, y: start.y - 2 }]);
  if (term.includes('drag') || term.includes('shallow')) return boundedPoints([start, { x, y: start.y - 2 }, { x: x + sign * 18, y: start.y - 2 }]);
  if (term.includes('slant') || term.includes('glance')) return boundedPoints([start, { x, y: start.y - stem }, { x: x + sign * 7, y: start.y - 10 }]);
  if (term.includes('out') || term.includes('sail')) return boundedPoints([start, { x, y: start.y - stem }, { x: x + sign * 8, y: start.y - stem }]);
  if (term.includes('dig') || term.includes('basic') || term.includes('in')) return boundedPoints([start, { x, y: start.y - 8 }, { x: x + sign * 10, y: start.y - 8 }]);
  if (term.includes('post')) return boundedPoints([start, { x, y: start.y - 8 }, { x: x + sign * 8, y: start.y - 14 }]);
  if (term.includes('corner') || term.includes('flag')) return boundedPoints([start, { x, y: start.y - 8 }, { x: x + sign * 10, y: start.y - 14 }]);
  if (term.includes('wheel') || term.includes('rail')) return boundedPoints([start, { x: x + sign * 4, y: start.y - 2 }, { x: x + sign * 5, y: start.y - 8 }, { x: x + sign * 9, y: start.y - 14 }]);
  if (term.includes('curl') || term.includes('hook') || term.includes('comeback')) return boundedPoints([start, { x, y: start.y - 8 }, { x: x - sign * 2, y: start.y - 7 }]);
  return boundedPoints([start, { x, y: start.y - 7 }, { x: x + sign * 6, y: start.y - 11 }]);
}

function defensivePath(start: Point, asset: PlayAsset, sign: number): Point[] {
  const term = token(asset);
  if (asset.kind === 'rush' || asset.kind === 'stunt' || term.includes('blitz') || term.includes('rush')) {
    const inside = term.includes('tex') || term.includes('twist');
    return boundedPoints([start, { x: start.x + (inside ? sign * 3 : sign), y: start.y + 5 }, { x: start.x + (inside ? sign * 7 : sign * 4), y: start.y + 11 }]);
  }
  if (asset.kind === 'fit' || term.includes('fit') || term.includes('spill') || term.includes('box')) return boundedPoints([start, { x: start.x + sign * 3, y: start.y + 5 }, { x: start.x + sign * 8, y: start.y + 8 }]);
  if (asset.kind === 'rotation' || term.includes('rotate') || term.includes('roll')) return boundedPoints([start, { x: start.x + sign * 5, y: start.y - 2 }, { x: start.x + sign * 12, y: start.y - 7 }]);
  if (asset.kind === 'coverage' || term.includes('cover') || term.includes('match') || term.includes('drop')) return boundedPoints([start, { x: start.x + sign * 3, y: start.y - 5 }, { x: start.x + sign * 8, y: start.y - 10 }]);
  return boundedPoints([start, { x: start.x + sign * 3, y: start.y - 4 }, { x: start.x + sign * 7, y: start.y - 7 }]);
}

function landmark(asset: PlayAsset): string | undefined {
  const term = token(asset);
  if (term.includes('flat') || term.includes('swing') || term.includes('arrow')) return 'Flat landmark';
  if (term.includes('dig') || term.includes('basic') || term.includes('in')) return 'Break at depth';
  if (term.includes('post') || term.includes('corner') || term.includes('flag') || term.includes('wheel')) return 'Vertical stem then break';
  if (term.includes('slant') || term.includes('glance')) return 'Quick inside landmark';
  if (asset.kind === 'run') return 'Aim at declared aiming point';
  if (asset.kind === 'block' || asset.kind === 'protection') return 'Declare leverage and fit point';
  if (asset.kind === 'coverage') return 'Carry threat to zone landmark';
  if (asset.kind === 'rush' || asset.kind === 'stunt') return 'Rush landmark through assigned gap';
  return undefined;
}

function depth(asset: PlayAsset): number | undefined {
  const term = token(asset);
  if (term.includes('go') || term.includes('vertical')) return 18;
  if (term.includes('post') || term.includes('corner') || term.includes('dig') || term.includes('basic')) return 12;
  if (term.includes('slant') || term.includes('glance') || term.includes('flat') || term.includes('drag')) return 5;
  if (asset.kind === 'coverage') return 10;
  return undefined;
}

export function materializeAssetAction(design: PlayDesign, player: PlayPlayer, asset: PlayAsset): PlayElement {
  const start = player.start ?? { x: 50, y: 26.5 };
  const sign = directionSign(design);
  const points = design.unit === 'defense' ? defensivePath(start, asset, sign) : offensivePath(start, asset, sign);
  const guide = Number(asset.default_timing_ms ?? (asset.kind === 'motion' ? 700 : asset.kind === 'block' || asset.kind === 'rush' ? 1800 : 1200));
  const startMs = asset.kind === 'motion' ? -Math.min(1200, guide) : 0;
  const endMs = asset.kind === 'motion' ? 0 : guide;
  const id = `EL-${asset.id}-${player.id}-${Date.now().toString(36).toUpperCase()}`;
  return {
    id,
    kind: asset.kind,
    type: asset.term,
    player_id: player.id,
    asset_id: asset.id,
    points,
    arrow_style: asset.arrow_style ?? asset.kind,
    arrow_ends: 'end',
    path_mode: asset.kind === 'block' || asset.kind === 'protection' || asset.kind === 'fit' ? 'sharp' : 'smooth',
    line_style: asset.kind === 'motion' ? 'dashed' : 'solid',
    stroke_width: 0.26,
    line_cap: 'round',
    assignment: asset.description ?? asset.accessibility ?? `${asset.term} assignment for ${player.position ?? player.id}`,
    note: asset.accessibility,
    landmark: landmark(asset),
    depth_yards: depth(asset),
    phase: asset.kind === 'motion' ? 'pre_snap' : 'post_snap',
    start_ms: startMs,
    end_ms: endMs,
    timing: { start_ms: startMs, end_ms: endMs, phases: defaultTimelinePhases(asset.kind, startMs, endMs) },
  };
}
