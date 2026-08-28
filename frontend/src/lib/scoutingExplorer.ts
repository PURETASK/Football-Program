import type { FootballRecord } from '../types';

export const TENDENCY_DIMENSIONS = [
  'down',
  'distance',
  'field_zone',
  'personnel',
  'formation',
  'motion',
  'front',
  'coverage',
  'pressure',
] as const;

export type TendencyDimension = typeof TENDENCY_DIMENSIONS[number];
export type TendencyReviewGate = 'contradiction' | 'low_sample' | 'missing_evidence' | 'low_confidence' | 'ready_for_staff_review';

export interface TendencyExplorerRecord {
  id: string;
  report_id: string;
  opponent?: string;
  statement: string;
  confidence: string;
  evidence_refs: string[];
  source_clips: string[];
  contradictions: string[];
  sample_size: number;
  trend?: string;
  stance?: string;
  review_gate: TendencyReviewGate;
  down: string;
  distance: string;
  field_zone: string;
  personnel: string;
  formation: string;
  motion: string;
  front: string;
  coverage: string;
  pressure: string;
}

function asObject(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function strings(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(strings);
  if (typeof value === 'string') return value.split(',').map((item) => item.trim()).filter(Boolean);
  if (typeof value === 'number' || typeof value === 'boolean') return [String(value)];
  const item = asObject(value);
  if (item.id || item.ref || item.reference || item.uri || item.title || item.statement) {
    return [String(item.id || item.ref || item.reference || item.uri || item.title || item.statement)];
  }
  return [];
}

function firstValue(...values: unknown[]): unknown {
  return values.find((value) => value !== undefined && value !== null && value !== '') ?? undefined;
}

function text(value: unknown, fallback: string): string {
  const result = strings(value)[0];
  return result || fallback;
}

function numeric(value: unknown): number {
  const result = Number(value);
  return Number.isFinite(result) ? result : 0;
}

function normalizedStance(value: unknown): string | undefined {
  const result = text(value, '');
  return result ? result.toLowerCase().replaceAll('-', '_').replaceAll(' ', '_') : undefined;
}

function explicitValues(item: Record<string, unknown>, report: FootballRecord, keys: string[], nested: Record<string, unknown>): string[] {
  return keys.flatMap((key) => strings(firstValue(item[key], report[key], nested[key])));
}

function gateFor(sampleSize: number, confidence: string, evidenceRefs: string[], contradictions: string[]): TendencyReviewGate {
  if (contradictions.length) return 'contradiction';
  if (sampleSize < 10) return 'low_sample';
  if (!evidenceRefs.length) return 'missing_evidence';
  if (['low', 'unrated', 'unknown', 'not_set'].includes(confidence.toLowerCase())) return 'low_confidence';
  return 'ready_for_staff_review';
}

function groupKey(record: Pick<TendencyExplorerRecord, 'opponent' | 'down' | 'distance' | 'field_zone' | 'personnel' | 'formation' | 'motion' | 'front' | 'coverage' | 'pressure'>): string {
  return [record.opponent || 'unknown', ...TENDENCY_DIMENSIONS.map((dimension) => record[dimension])].map((value) => String(value).toLowerCase()).join('|');
}

/**
 * Build a conservative, source-preserving tendency index from scouting reports.
 * Contradictions are only inferred when records provide an explicit stance;
 * natural-language claims are never treated as opposites by string matching.
 */
export function buildTendencyExplorerRecords(reports: FootballRecord[]): TendencyExplorerRecord[] {
  const draftRecords = reports.flatMap((report) => {
    const situation = asObject(report.situation);
    const tags = asObject(report.tags);
    const evolution = asObject(firstValue(report.evolution, report.adaptation, report.trend_context));
    const claims: unknown[] = Array.isArray(report.claims)
      ? report.claims
      : [{ statement: firstValue(report.claims, report.title, report.id), confidence: report.confidence, evidence_refs: report.evidence_refs }];

    return claims.map((claim, index): TendencyExplorerRecord => {
      const item = asObject(claim);
      const dimension = (key: TendencyDimension) => text(firstValue(item[key], situation[key], tags[key], report[key]), 'all');
      const evidenceRefs = explicitValues(item, report, ['evidence_refs', 'source_refs', 'sources'], {});
      const sourceClips = explicitValues(item, report, ['source_clips', 'clip_ids', 'film_clip_ids', 'film_clips'], {});
      const explicitContradictions = explicitValues(item, report, ['contradictions', 'contradicts', 'conflicts', 'contradiction_refs'], {});
      const trend = text(firstValue(item.trend, item.trend_direction, item.evolution, item.current_vs_historical, report.trend, report.trend_direction, evolution.trend, evolution.direction), '');
      const stance = normalizedStance(firstValue(item.stance, item.direction, item.polarity, report.stance));
      const confidence = text(firstValue(item.confidence, report.confidence), 'unrated');
      const sampleSize = numeric(firstValue(item.sample_size, report.sample_size));

      return {
        id: `${report.id}-CLAIM-${index + 1}`,
        report_id: report.id,
        opponent: report.opponent,
        statement: text(firstValue(item.statement, item.claim, item.description), 'Unlabeled tendency'),
        confidence,
        evidence_refs: [...new Set(evidenceRefs)],
        source_clips: [...new Set(sourceClips)],
        contradictions: [...new Set(explicitContradictions)],
        sample_size: sampleSize,
        trend: trend || undefined,
        stance,
        review_gate: 'ready_for_staff_review',
        down: dimension('down'),
        distance: dimension('distance'),
        field_zone: dimension('field_zone'),
        personnel: dimension('personnel'),
        formation: dimension('formation'),
        motion: dimension('motion'),
        front: dimension('front'),
        coverage: dimension('coverage'),
        pressure: dimension('pressure'),
      };
    });
  });

  const groups = new Map<string, TendencyExplorerRecord[]>();
  for (const record of draftRecords) {
    const group = groups.get(groupKey(record)) ?? [];
    group.push(record);
    groups.set(groupKey(record), group);
  }

  return draftRecords.map((record) => {
    const group = groups.get(groupKey(record)) ?? [];
    const opposingClaims = record.stance
      ? group.filter((candidate) => candidate.id !== record.id && candidate.stance && candidate.stance !== record.stance).map((candidate) => candidate.id)
      : [];
    const contradictions = [...new Set([...record.contradictions, ...opposingClaims])];
    const evidenceRefs = [...new Set([...record.evidence_refs, ...record.source_clips])];
    return {
      ...record,
      contradictions,
      review_gate: gateFor(record.sample_size, record.confidence, evidenceRefs, contradictions),
    };
  });
}
