import type { PlayDesign, PlayElement, Point } from '../types';

export interface CoverageShellBox {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface CoverageShellLink {
  id: string;
  zone: string;
  owner: string;
  kind: 'coverage' | 'rotation';
  from: Point;
  to: Point;
  sequence?: number;
  conflict: boolean;
  startMs: number;
  endMs: number;
}

const BOXES: Record<string, CoverageShellBox> = {
  deep_left: { id: 'deep_left', label: 'Deep left', x: 1, y: 1, width: 32, height: 14 },
  deep_middle: { id: 'deep_middle', label: 'Deep middle', x: 34, y: 1, width: 32, height: 14 },
  deep_right: { id: 'deep_right', label: 'Deep right', x: 67, y: 1, width: 32, height: 14 },
  deep_half_left: { id: 'deep_half_left', label: 'Deep half left', x: 1, y: 1, width: 48, height: 14 },
  deep_half_right: { id: 'deep_half_right', label: 'Deep half right', x: 51, y: 1, width: 48, height: 14 },
  flat_left: { id: 'flat_left', label: 'Flat left', x: 1, y: 15.5, width: 25, height: 12 },
  flat_right: { id: 'flat_right', label: 'Flat right', x: 74, y: 15.5, width: 25, height: 12 },
  hook_curl_left: { id: 'hook_curl_left', label: 'Hook/curl left', x: 20, y: 15.5, width: 28, height: 12 },
  hook_curl_middle: { id: 'hook_curl_middle', label: 'Hook/curl middle', x: 36, y: 15.5, width: 28, height: 12 },
  hook_curl_right: { id: 'hook_curl_right', label: 'Hook/curl right', x: 52, y: 15.5, width: 28, height: 12 },
  robber: { id: 'robber', label: 'Robber / low hole', x: 38, y: 27.5, width: 24, height: 12 },
  bracket: { id: 'bracket', label: 'Bracket / double', x: 26, y: 8, width: 48, height: 28 },
  man: { id: 'man', label: 'Man coverage', x: 1, y: 1, width: 98, height: 38 },
};

export const COVERAGE_SHELL_OPTIONS = Object.values(BOXES);

export function coverageShellBoxes(zones: string[] | undefined): CoverageShellBox[] {
  const seen = new Set<string>();
  return (zones ?? []).map((zone) => BOXES[zone]).filter((box): box is CoverageShellBox => {
    if (!box || seen.has(box.id)) return false;
    seen.add(box.id);
    return true;
  });
}

export function coverageShellAnchor(zone: string): Point | undefined {
  const box = BOXES[zone];
  return box ? { x: box.x + box.width / 2, y: box.y + box.height / 2 } : undefined;
}

/** Return every assignment that declares ownership of each visual shell zone. */
export function coverageShellOwners(design: Pick<PlayDesign, 'elements'>): Map<string, string[]> {
  const owners = new Map<string, string[]>();
  for (const element of design.elements ?? []) {
    if (element.kind !== 'coverage' && element.kind !== 'rotation') continue;
    const zone = element.kind === 'rotation' ? element.rotation_to_zone ?? element.zone : element.zone;
    if (!zone) continue;
    const list = owners.get(zone) ?? [];
    list.push(element.player_id ?? element.type ?? element.id);
    owners.set(zone, list);
  }
  return owners;
}

/** Build explicit owner-to-destination vectors for the visual coverage shell. */
export function coverageShellLinks(design: PlayDesign): CoverageShellLink[] {
  const owners = coverageShellOwners(design);
  return (design.elements ?? []).flatMap((element) => {
    if (element.kind !== 'coverage' && element.kind !== 'rotation') return [];
    const zone = element.kind === 'rotation' ? element.rotation_to_zone ?? element.zone : element.zone;
    if (!zone) return [];
    const to = coverageShellAnchor(zone);
    if (!to) return [];
    const from = element.points?.at(-1) ?? element.path?.at(-1) ?? (element.player_id ? design.players?.find((player) => player.id === element.player_id)?.start : undefined);
    if (!from) return [];
    return [{
      id: `${element.id}::shell`,
      zone,
      owner: element.player_id ?? element.type ?? element.id,
      kind: element.kind,
      from,
      to,
      sequence: element.kind === 'rotation' && element.rotation_sequence !== undefined ? element.rotation_sequence : undefined,
      conflict: (owners.get(zone)?.length ?? 0) > 1,
      startMs: Number(element.start_ms ?? element.timing?.start_ms ?? 0),
      endMs: Number(element.end_ms ?? element.timing?.end_ms ?? 3000),
    }];
  });
}

/** Connect a coverage/rotation assignment to an explicit shell destination. */
export function coverageMovementPatch(element: PlayElement, design: PlayDesign, zone: string): Partial<PlayElement> {
  const anchor = coverageShellAnchor(zone);
  const next: Partial<PlayElement> = { zone: zone || undefined, rotation_to_zone: element.kind === 'rotation' ? zone || undefined : element.rotation_to_zone, phase: element.kind === 'rotation' ? 'rotation' : 'coverage', movement_geometry: 'shell-targeted' };
  const existing = element.points ?? element.path ?? [];
  const source = existing[0] ?? (element.player_id ? design.players?.find((player) => player.id === element.player_id)?.start : undefined);
  if (!anchor || !source || existing.length >= 2) return next;
  const midpoint = { x: (source.x + anchor.x) / 2, y: (source.y + anchor.y) / 2 };
  const points = [source, midpoint, anchor];
  if (element.points) next.points = points;
  else next.path = points;
  return next;
}
