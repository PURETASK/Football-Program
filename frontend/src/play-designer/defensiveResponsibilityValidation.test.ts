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

  it('surfaces multi-owner shell/gap responsibilities and incomplete rotations', () => {
    const design: PlayDesign = { id: 'OWNERS', unit: 'defense', coverage_zones: ['flat_left'], players: [{ id: 'CB', position: 'CB' }], elements: [
      { id: 'DROP-1', kind: 'coverage', player_id: 'CB', zone: 'flat_left' },
      { id: 'DROP-2', kind: 'rotation', player_id: 'SS', rotation_to_zone: 'flat_left', rotation_sequence: 0, rotation_replacement_player_id: 'MISSING' },
      { id: 'FIT-1', kind: 'fit', player_id: 'MIKE', gap_owner: 'left_b' },
      { id: 'FIT-2', kind: 'fit', player_id: 'WILL', gap_owner: 'left_b' },
    ] };
    const codes = defensiveResponsibilityIssues(design).map((finding) => finding.code);
    expect(codes).toEqual(expect.arrayContaining(['SHELL_ZONE_MULTI_OWNER', 'GAP_OWNERSHIP_CONFLICT', 'ROTATION_TRIGGER_MISSING', 'ROTATION_SEQUENCE_INVALID', 'ROTATION_REPLACEMENT_PLAYER_MISSING', 'ROTATION_VACATED_ZONE_MISSING']));
  });
});
