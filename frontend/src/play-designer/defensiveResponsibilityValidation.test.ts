import { describe, expect, it } from 'vitest';

import type { PlayDesign } from '../types';
import { defensiveResponsibilityIssues } from './defensiveResponsibilityValidation';

describe('defensive responsibility validation', () => {
  it('finds non-reciprocal exchanges, missing replacement ownership, and duplicate sequence numbers', () => {
    const design: PlayDesign = { id: 'CHECKS', unit: 'defense', coverage_zones: ['flat_left'], elements: [
      { id: 'RUSH', kind: 'rush', exchange_with: 'DROP', exchange_role: 'rush_replace', rotation_sequence: 1 },
      { id: 'ROTATE', kind: 'rotation', rotation_sequence: 1 },
    ] };
    const codes = defensiveResponsibilityIssues(design).map((finding) => finding.code);
    expect(codes).toEqual(expect.arrayContaining(['EXCHANGE_PARTNER_MISSING', 'ROTATION_SEQUENCE_DUPLICATE', 'SHELL_ZONE_UNOWNED']));
  });

  it('accepts a reciprocal rush/replace pair with a replacement zone', () => {
    const design: PlayDesign = { id: 'VALID', unit: 'defense', elements: [
      { id: 'RUSH', kind: 'rush', exchange_with: 'DROP', exchange_role: 'rush_replace' },
      { id: 'DROP', kind: 'coverage', exchange_with: 'RUSH', exchange_role: 'drop_replace', rotation_to_zone: 'flat_left', zone: 'flat_left' },
    ] };
    expect(defensiveResponsibilityIssues(design).some((finding) => finding.code === 'EXCHANGE_PARTNER_MISSING' || finding.code === 'REPLACEMENT_OWNER_MISSING')).toBe(false);
  });

  it('requires a synchronized exchange cue for an otherwise complete pair', () => {
    const design: PlayDesign = { id: 'TIMELINE', unit: 'defense', elements: [
      { id: 'RUSH', kind: 'rush', exchange_with: 'DROP', exchange_role: 'rush_replace' },
      { id: 'DROP', kind: 'coverage', exchange_with: 'RUSH', exchange_role: 'drop_replace', rotation_to_zone: 'flat_left' },
    ], timeline: { duration_ms: 2500, events: [] } };
    expect(defensiveResponsibilityIssues(design).map((finding) => finding.code)).toContain('EXCHANGE_TIMELINE_MISSING');
    const synchronized = { ...design, timeline: { duration_ms: 2500, events: [{ id: 'EX', kind: 'exchange', element_id: 'RUSH', start_ms: 250, end_ms: 700 }] } };
    expect(defensiveResponsibilityIssues(synchronized).map((finding) => finding.code)).not.toContain('EXCHANGE_TIMELINE_MISSING');
    const blockRushSynchronized = { ...design, timeline: { duration_ms: 2500, events: [{ id: 'BR', kind: 'rush_exchange', element_id: 'RUSH', start_ms: 250, end_ms: 700 }] } };
    expect(defensiveResponsibilityIssues(blockRushSynchronized).map((finding) => finding.code)).not.toContain('EXCHANGE_TIMELINE_MISSING');
  });
});
