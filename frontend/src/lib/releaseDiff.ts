import type { GamePlanReleaseSnapshot } from '../types';

export interface ReleaseFieldChange {
  path: string;
  before: string;
  after: string;
  kind: 'added' | 'removed' | 'changed';
}

function objectValue(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function display(value: unknown): string {
  if (value === undefined) return 'Not present';
  if (value === null) return 'None';
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.length ? value.map(display).join(', ') : 'Empty list';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function flatten(value: unknown, path: string, output: Map<string, string>, depth = 0): void {
  if (Array.isArray(value) || depth >= 2 || typeof value !== 'object' || value === null) {
    output.set(path, display(value));
    return;
  }
  const entries = Object.entries(value as Record<string, unknown>);
  if (!entries.length) output.set(path, 'Empty object');
  for (const [key, child] of entries) flatten(child, path ? `${path}.${key}` : key, output, depth + 1);
}

/** Compare the frozen source-plan payloads, never mutable live records. */
export function compareReleaseSnapshots(base?: GamePlanReleaseSnapshot | null, current?: GamePlanReleaseSnapshot | null): ReleaseFieldChange[] {
  if (!current) return [];
  const before = new Map<string, string>();
  const after = new Map<string, string>();
  flatten(objectValue(base?.source_plan), '', before);
  flatten(objectValue(current.source_plan), '', after);
  const paths = [...new Set([...before.keys(), ...after.keys()])].sort();
  return paths.flatMap((path) => {
    const prior = before.get(path);
    const next = after.get(path);
    if (prior === next) return [];
    return [{ path, before: prior ?? 'Not present', after: next ?? 'Not present', kind: prior === undefined ? 'added' : next === undefined ? 'removed' : 'changed' }];
  });
}
