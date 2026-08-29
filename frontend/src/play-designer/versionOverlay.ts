import type { PlayElement, PlayPlayer } from '../types';

export type VersionChange = 'added' | 'changed' | 'removed' | 'unchanged';

interface VersionObject {
  id: string;
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value as Record<string, unknown>).sort().map((key) => [key, stableValue((value as Record<string, unknown>)[key])]));
  }
  return value;
}

function fingerprint(value: VersionObject | undefined): string {
  if (!value) return '';
  return JSON.stringify(stableValue(value));
}

function changeMap<T extends VersionObject>(current: T[], compare: T[]): Map<string, VersionChange> {
  const compareById = new Map(compare.map((item) => [item.id, item]));
  return new Map(current.map((item) => {
    const previous = compareById.get(item.id);
    return [item.id, previous ? (fingerprint(item) === fingerprint(previous) ? 'unchanged' : 'changed') : 'added'];
  }));
}

/** Return deterministic field-overlay states for the current and compared snapshots. */
export function versionOverlayChanges(current: { elements?: PlayElement[]; players?: PlayPlayer[] }, compare?: { elements?: PlayElement[]; players?: PlayPlayer[] }): {
  elements: Map<string, VersionChange>;
  players: Map<string, VersionChange>;
  removedElements: Set<string>;
  removedPlayers: Set<string>;
} {
  const currentElements = current.elements ?? [];
  const compareElements = compare?.elements ?? [];
  const currentPlayers = current.players ?? [];
  const comparePlayers = compare?.players ?? [];
  const currentElementIds = new Set(currentElements.map((item) => item.id));
  const currentPlayerIds = new Set(currentPlayers.map((item) => item.id));
  return {
    elements: changeMap(currentElements, compareElements),
    players: changeMap(currentPlayers, comparePlayers),
    removedElements: new Set(compareElements.filter((item) => !currentElementIds.has(item.id)).map((item) => item.id)),
    removedPlayers: new Set(comparePlayers.filter((item) => !currentPlayerIds.has(item.id)).map((item) => item.id)),
  };
}

export function versionChangeLabel(change: VersionChange): string {
  return change === 'added' ? 'added in current version' : change === 'changed' ? 'changed from compared version' : change === 'removed' ? 'removed from current version' : 'unchanged from compared version';
}
