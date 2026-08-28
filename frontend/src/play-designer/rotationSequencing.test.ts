import { describe, expect, it } from 'vitest';
import { rotationLabel, rotationSequencePatch } from './rotationSequencing';

describe('defensive rotation sequencing', () => {
  it('stores a normalized rotation sequence patch in the rotation phase', () => {
    expect(rotationSequencePatch({ rotation_trigger: 'motion', rotation_to_zone: 'flat_right', rotation_sequence: 2 })).toEqual({ rotation_trigger: 'motion', rotation_to_zone: 'flat_right', rotation_sequence: 2, phase: 'rotation' });
  });
  it('produces a coach-readable trigger and destination label', () => {
    expect(rotationLabel({ id: 'ROT', kind: 'rotation', rotation_trigger: 'snap', rotation_to_zone: 'deep_half_left' })).toBe('At snap → deep_half_left');
  });
});
