import type { PlayDesign, PlayElement } from '../types';

export const DEFENSIVE_GAP_OPTIONS = [
  ['left_edge', 'Left edge / contain'], ['left_c', 'Left C gap'], ['left_b', 'Left B gap'], ['left_a', 'Left A gap'],
  ['right_a', 'Right A gap'], ['right_b', 'Right B gap'], ['right_c', 'Right C gap'], ['right_edge', 'Right edge / contain'],
  ['left_force', 'Left force'], ['right_force', 'Right force'], ['left_cutback', 'Left cutback'], ['right_cutback', 'Right cutback'],
] as const;

const GAP_X: Record<string, number> = {
  left_edge: 5, left_c: 15, left_b: 25, left_a: 36, right_a: 64, right_b: 75, right_c: 85, right_edge: 95,
  left_force: 10, right_force: 90, left_cutback: 43, right_cutback: 57,
};

export interface DefensiveGapLink {
  gap: string;
  label: string;
  x: number;
  owner?: string;
  elementId?: string;
  conflict: boolean;
  anchor?: { x: number; y: number };
}

export interface DefensiveGapSummary {
  total: number;
  owned: number;
  unassigned: number;
  conflicts: number;
  status: 'ready' | 'review';
}

export function gapOwnerPatch(value: string): Partial<PlayElement> {
  const label = DEFENSIVE_GAP_OPTIONS.find(([key]) => key === value)?.[1] ?? value;
  return { gap_owner: value || undefined, gap_owner_label: value ? label : undefined, gap: value || undefined, fit_gap: value || undefined };
}

export function defensiveGapOwners(design: PlayDesign): Map<string, { elementId: string; owner: string; conflict: boolean }> {
  const byGap = new Map<string, PlayElement[]>();
  for (const element of design.elements ?? []) {
    const gap = typeof element.gap_owner === 'string' ? element.gap_owner : undefined;
    if (!gap) continue;
    const list = byGap.get(gap) ?? [];
    list.push(element);
    byGap.set(gap, list);
  }
  return new Map([...byGap.entries()].map(([gap, elements]) => [gap, {
    elementId: elements[0].id,
    owner: elements.map((element) => element.player_id ?? element.type ?? element.kind).join(' + '),
    conflict: elements.length > 1 && new Set(elements.map((element) => element.responsibility ?? element.objective ?? element.kind)).size > 1,
  }]));
}

export function defensiveGapLinks(design: PlayDesign): DefensiveGapLink[] {
  const owners = defensiveGapOwners(design);
  return DEFENSIVE_GAP_OPTIONS.map(([gap, label]) => {
    const owner = owners.get(gap);
    const element = owner ? (design.elements ?? []).find((item) => item.id === owner.elementId) : undefined;
    const points = element?.points ?? [];
    const anchor = points.length ? points[points.length - 1] : undefined;
    return { gap, label, x: GAP_X[gap], owner: owner?.owner, elementId: owner?.elementId, conflict: owner?.conflict ?? false, anchor };
  });
}

export function defensiveGapSummary(design: PlayDesign): DefensiveGapSummary {
  const links = defensiveGapLinks(design);
  const owned = links.filter((link) => Boolean(link.owner));
  const conflicts = links.filter((link) => link.conflict);
  return { total: links.length, owned: owned.length, unassigned: links.length - owned.length, conflicts: conflicts.length, status: conflicts.length || owned.length < links.length ? 'review' : 'ready' };
}
