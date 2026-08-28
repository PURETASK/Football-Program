import { compareReleaseSnapshots } from './releaseDiff';

describe('release snapshot comparison', () => {
  it('compares frozen source-plan fields and classifies additions, removals, and changes', () => {
    const changes = compareReleaseSnapshots(
      { id: 'R-1', plan_id: 'GP-1', week: 'WEEK-1', status: 'approved', source_plan: { offense: { opening_script: ['run'] }, defense: 'quarters', old_field: true } },
      { id: 'R-2', plan_id: 'GP-1', week: 'WEEK-1', status: 'pending_approval', source_plan: { offense: { opening_script: ['pass'] }, defense: 'quarters', new_field: 'counter' } },
    );

    expect(changes).toEqual([
      { path: 'new_field', before: 'Not present', after: 'counter', kind: 'added' },
      { path: 'offense.opening_script', before: 'run', after: 'pass', kind: 'changed' },
      { path: 'old_field', before: 'true', after: 'Not present', kind: 'removed' },
    ]);
  });

  it('returns no changes when the source plans are equivalent', () => {
    expect(compareReleaseSnapshots(
      { id: 'R-1', plan_id: 'GP-1', week: 'WEEK-1', status: 'approved', source_plan: { offense: 'balanced' } },
      { id: 'R-2', plan_id: 'GP-1', week: 'WEEK-1', status: 'pending_approval', source_plan: { offense: 'balanced' } },
    )).toEqual([]);
  });
});
