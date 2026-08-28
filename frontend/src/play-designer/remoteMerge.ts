import type { PlayDesign, PlayElement, PlayPlayer } from '../types';

export interface RemoteMergeResult {
  status: 'merged' | 'conflict';
  design?: PlayDesign;
  conflictPaths: string[];
}

function equal(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Merge nested object fields so independent edits on one route/player converge. */
function mergeValue(path: string, base: unknown, local: unknown, remote: unknown, conflicts: string[]): unknown {
  const localChanged = !equal(local, base);
  const remoteChanged = !equal(remote, base);
  if (!localChanged && !remoteChanged) return remote;
  if (localChanged && !remoteChanged) return local;
  if (!localChanged && remoteChanged) return remote;
  if (equal(local, remote)) return local;
  if (!isRecord(local) || !isRecord(remote)) {
    conflicts.push(path);
    return remote;
  }

  const merged: Record<string, unknown> = { ...remote };
  const keys = new Set([...Object.keys(isRecord(base) ? base : {}), ...Object.keys(local), ...Object.keys(remote)]);
  for (const key of keys) {
    const value = mergeValue(`${path}.${key}`, isRecord(base) ? base[key] : undefined, local[key], remote[key], conflicts);
    if (value === undefined) delete merged[key];
    else merged[key] = value;
  }
  return merged;
}

function mergeCollection<T extends { id: string }>(key: 'players' | 'elements', base: T[], local: T[], remote: T[], conflicts: string[]): T[] {
  const baseById = new Map(base.map((item) => [item.id, item]));
  const localById = new Map(local.map((item) => [item.id, item]));
  const remoteById = new Map(remote.map((item) => [item.id, item]));
  const ids = [...new Set([...remote.map((item) => item.id), ...local.map((item) => item.id)])];
  const output: T[] = [];
  for (const id of ids) {
    const chosen = mergeValue(`${key}.${id}`, baseById.get(id), localById.get(id), remoteById.get(id), conflicts);
    if (chosen) output.push(chosen as T);
  }
  return output;
}

/** Three-way merge local unsaved work with a newer server revision. */
export function mergeRemoteDesign(base: PlayDesign | undefined, local: PlayDesign, remote: PlayDesign): RemoteMergeResult {
  if (!base || base.id !== local.id || local.id !== remote.id) return { status: 'conflict', conflictPaths: ['design.identity'] };
  const conflicts: string[] = [];
  const merged: PlayDesign = { ...remote };
  const excluded = new Set(['id', '_revision', 'players', 'elements', 'validation', 'status', 'approval', 'version', 'updated_at']);
  const keys = new Set([...Object.keys(base), ...Object.keys(local), ...Object.keys(remote)]);
  for (const key of keys) {
    if (excluded.has(key)) continue;
    const value = mergeValue(key, base[key], local[key], remote[key], conflicts);
    if (value === undefined) delete (merged as Record<string, unknown>)[key];
    else (merged as Record<string, unknown>)[key] = value;
  }
  merged.players = mergeCollection('players', base.players ?? [], local.players ?? [], remote.players ?? [], conflicts) as PlayPlayer[];
  merged.elements = mergeCollection('elements', base.elements ?? [], local.elements ?? [], remote.elements ?? [], conflicts) as PlayElement[];
  if (conflicts.length) return { status: 'conflict', conflictPaths: conflicts };
  return { status: 'merged', design: merged, conflictPaths: [] };
}
