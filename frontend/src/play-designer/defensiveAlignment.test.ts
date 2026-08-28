import { describe, expect, it } from 'vitest';
import { defensiveAlignmentLabel, defensiveAlignmentPatch } from './defensiveAlignment';

describe('defensive front technique authoring', () => {
  it('stores technique, relationship, and a canonical alignment key', () => {
    expect(defensiveAlignmentPatch('3', 'outside_eye')).toEqual({ defensive_technique: '3', defensive_alignment: 'outside_eye', alignment_key: '3:outside_eye' });
  });
  it('renders a readable alignment label', () => {
    expect(defensiveAlignmentLabel({ id: 'DT', defensive_technique: '4i', defensive_alignment: 'inside_shade' })).toBe('4i-tech · inside shade');
  });
});
