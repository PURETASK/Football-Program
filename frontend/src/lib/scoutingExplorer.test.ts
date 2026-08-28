import { buildTendencyExplorerRecords } from './scoutingExplorer';

describe('scouting tendency explorer', () => {
  it('preserves explicit dimensions, trends, source clips, and review gates', () => {
    const [record] = buildTendencyExplorerRecords([{
      id: 'SCOUT-1',
      opponent: 'OPP-1',
      sample_size: 24,
      confidence: 'high',
      situation: { down: 3, distance: 'long', field_zone: 'high_red_zone' },
      tags: { personnel: '11', formation: 'trips', motion: 'jet' },
      claims: [{ statement: 'Trips motion produces a pressure check.', stance: 'increase', trend: 'rising', source_clips: ['CLIP-22'] }],
      evidence_refs: ['FILM-OBS-9'],
    }]);

    expect(record.statement).toContain('pressure check');
    expect(record.down).toBe('3');
    expect(record.personnel).toBe('11');
    expect(record.trend).toBe('rising');
    expect(record.source_clips).toEqual(['CLIP-22']);
    expect(record.evidence_refs).toEqual(['FILM-OBS-9']);
    expect(record.review_gate).toBe('ready_for_staff_review');
  });

  it('only infers contradictions from explicit opposing stances', () => {
    const records = buildTendencyExplorerRecords([{
      id: 'SCOUT-2',
      opponent: 'OPP-1',
      sample_size: 20,
      confidence: 'moderate',
      situation: { down: 2, distance: 'medium' },
      claims: [
        { statement: 'Claim A', stance: 'increase', evidence_refs: ['CLIP-A'] },
        { statement: 'Claim B', stance: 'decrease', evidence_refs: ['CLIP-B'] },
        { statement: 'Claim C', evidence_refs: ['CLIP-C'] },
      ],
    }]);

    expect(records[0].contradictions).toContain('SCOUT-2-CLAIM-2');
    expect(records[1].contradictions).toContain('SCOUT-2-CLAIM-1');
    expect(records[2].contradictions).toEqual([]);
  });

  it('prioritizes evidence risk gates in an explainable order', () => {
    const records = buildTendencyExplorerRecords([
      { id: 'LOW-SAMPLE', sample_size: 4, confidence: 'high', evidence_refs: ['CLIP-1'], claims: [{ statement: 'Small sample' }] },
      { id: 'NO-EVIDENCE', sample_size: 14, confidence: 'high', claims: [{ statement: 'No source' }] },
      { id: 'LOW-CONFIDENCE', sample_size: 14, confidence: 'low', evidence_refs: ['CLIP-3'], claims: [{ statement: 'Low confidence' }] },
    ]);

    expect(records.map((record) => record.review_gate)).toEqual(['low_sample', 'missing_evidence', 'low_confidence']);
  });
});
