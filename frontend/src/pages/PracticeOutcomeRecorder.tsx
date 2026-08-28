import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CircleCheck, Gauge } from 'lucide-react';
import { useState, type FormEvent } from 'react';

import { MutationNotice } from '../components/OperationalWorkbench';
import { recordAnalyticsOutcome } from '../lib/api';
import { compactValue, recordId, splitList } from '../lib/format';
import type { AppSession, PracticePeriod, PracticePlan } from '../types';

export function PracticeOutcomeRecorder({ session, practice, canAuthor, onRecorded }: { session: AppSession; practice: PracticePlan; canAuthor: boolean; onRecorded: () => void }) {
  const queryClient = useQueryClient();
  const [periodId, setPeriodId] = useState(practice.periods?.[0]?.id || '');
  const period = practice.periods?.find((candidate) => candidate.id === periodId) || practice.periods?.[0];
  const mutation = useMutation({
    mutationFn: (values: Parameters<typeof recordAnalyticsOutcome>[1]) => recordAnalyticsOutcome(session, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics-workspace', session.organizationId] });
      onRecorded();
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!period) return;
    const form = new FormData(event.currentTarget);
    mutation.mutate({
      outcomeId: recordId('OUTCOME-'),
      intendedRecordType: 'practice_period',
      intendedRecordId: period.id,
      actualResult: String(form.get('actual_result') || 'not_scored'),
      successCount: Number(form.get('success_count') || 0),
      sampleSize: Number(form.get('sample_size') || period.reps || 0),
      context: {
        situation: String(form.get('situation') || 'practice_install'),
        practice_id: practice.id,
        period_id: period.id,
        install_phase: period.install_phase,
        play_ids: period.play_ids ?? [],
        drill_ids: period.drill_ids ?? [],
        position_groups: period.position_groups ?? [],
        responsibility_phase: String(form.get('responsibility_phase') || 'general'),
      },
      evidenceRefs: splitList(String(form.get('evidence_refs') || '')),
      linkedPlayId: period.play_ids?.[0],
      linkedAssignmentId: String(form.get('linked_assignment_id') || '') || undefined,
      teachingStepId: String(form.get('teaching_step_id') || '') || undefined,
      responsibilityPhase: String(form.get('responsibility_phase') || 'general'),
      practiceId: practice.id,
      filmObservationIds: splitList(String(form.get('film_observation_ids') || '')),
      notes: String(form.get('notes') || ''),
    });
  }

  if (!canAuthor) return <p className="approval-boundary">Practice outcome recording requires coaching, analyst, performance-staff, or owner authority.</p>;
  if (!period) return <div className="workbench-pane"><p className="workbench-form__hint">Create a practice period before recording a practice outcome.</p></div>;

  return (
    <form className="workbench-form workbench-pane" onSubmit={submit}>
      <div className="workbench-pane__header"><div><h3><Gauge aria-hidden="true" size={16} /> Capture practice outcome</h3><p>Compare the period’s intended install objective with the observed rep result. This record feeds the Analytics outcome loop without activating the practice or changing player status.</p></div></div>
      <div className="workbench-form__grid">
        <label className="is-wide"><span>Practice plan</span><input aria-label="Practice plan" readOnly value={`${practice.id} · ${practice.objective || 'Practice install'}`} /></label>
        <label className="is-wide"><span>Installed period</span><select onChange={(event) => setPeriodId(event.target.value)} value={periodId}>{(practice.periods ?? []).map((candidate: PracticePeriod) => <option key={candidate.id} value={candidate.id}>{candidate.id} · {candidate.objective || candidate.type} · {candidate.reps} planned reps</option>)}</select></label>
        <label><span>Observed result</span><select defaultValue="not_scored" name="actual_result"><option>success</option><option>partial</option><option>failure</option><option>neutral</option><option>not_scored</option></select></label>
        <label><span>Successful reps</span><input min="0" name="success_count" required type="number" /></label>
        <label><span>Observed sample</span><input defaultValue={period.reps || 1} min="1" name="sample_size" required type="number" /></label>
        <label><span>Situation</span><input defaultValue="practice_install" name="situation" required /></label>
        <label className="is-wide"><span>Evidence references <small>comma separated; practice/period/clip refs</small></span><input defaultValue={[practice.id, period.id, ...(period.play_ids ?? []), ...(period.drill_ids ?? [])].join(', ')} name="evidence_refs" required /></label>
        <label className="is-wide"><span>Film observation IDs <small>optional, comma separated</small></span><input name="film_observation_ids" placeholder="FILM-OBS-…" /></label>
        <label><span>Responsibility phase</span><select defaultValue="general" name="responsibility_phase"><option value="general">General assignment</option><option value="read">Pre-snap read</option><option value="exchange">Exchange trigger</option><option value="replacement">Replacement / fit</option><option value="finish">Finish</option></select></label>
        <label><span>Assignment ID <small>optional</small></span><input name="linked_assignment_id" placeholder="RUSH-1 / DROP-1" /></label>
        <label><span>Teaching step ID <small>optional</small></span><input name="teaching_step_id" placeholder="STEP-…" /></label>
        <label className="is-wide"><span>Coach observation</span><textarea name="notes" placeholder={`What did staff observe about ${compactValue(period.coaching_objective || period.objective)}?`} /></label>
      </div>
      <div className="workbench-form__actions"><p className="workbench-form__hint">The server calculates confidence and Wilson uncertainty. Small samples and partial/failure results remain review-required.</p><button className="button button--primary" disabled={mutation.isPending} type="submit"><CircleCheck size={15} /> Save practice outcome</button></div>
      <MutationNotice error={mutation.error} pending={mutation.isPending} success={mutation.isSuccess} successMessage="Practice outcome recorded and linked to Analytics." />
    </form>
  );
}
