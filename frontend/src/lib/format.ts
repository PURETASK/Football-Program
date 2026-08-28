import type { FootballRecord } from '../types';

export function splitList(value: string): string[] {
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

export function recordLabel(record: Pick<FootballRecord, 'id' | 'name' | 'title'>): string {
  return record.name || record.title || record.id;
}

export function sentenceCase(value?: string): string {
  if (!value) return 'Not set';
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function compactValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Not set';
  if (Array.isArray(value)) {
    if (!value.length) return 'None';
    const visible = value.slice(0, 5).map(compactValue).join(' · ');
    return value.length > 5 ? `${visible} · +${value.length - 5} more` : visible;
  }
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .slice(0, 4)
      .map(([key, item]) => `${sentenceCase(key)}: ${compactValue(item)}`)
      .join(' · ');
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

export function recordId(prefix: string): string {
  const stamp = new Date().toISOString().replace(/\D/g, '').slice(0, 14);
  const random = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `${prefix}${stamp}-${random}`;
}

export function isoDate(): string {
  return new Date().toISOString().slice(0, 10);
}
