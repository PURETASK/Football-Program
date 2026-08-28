import { useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { CheckCircle2, GraduationCap, LoaderCircle, MessageCircleQuestion, X } from 'lucide-react';

import { useSession } from '../auth/SessionContext';
import { useModalFocusTrap } from '../hooks/useModalFocusTrap';
import { usePlayRoleViewQuery } from '../hooks/useWorkspaceData';
import { recordPlayMastery, submitPlayQuiz } from '../lib/api';
import type { PlayDesign, PlayRoleViewQuiz } from '../types';
import { TeachingDiagram } from './TeachingDiagram';

type TeachingMode = 'player' | 'position_group' | 'coach';

function optionLabel(option: unknown): string {
  if (typeof option === 'string' || typeof option === 'number') return String(option);
  if (option && typeof option === 'object') {
    const value = option as Record<string, unknown>;
    return String(value.label ?? value.name ?? value.value ?? value.id ?? 'Option');
  }
  return 'Option';
}

function optionValue(option: unknown): unknown {
  if (option && typeof option === 'object') {
    const value = option as Record<string, unknown>;
    return value.value ?? value.id ?? value.label ?? value.name;
  }
  return option;
}

function quizIsVisible(quiz: PlayRoleViewQuiz, revealedStepIds: Set<string>): boolean {
  return !quiz.step_id || revealedStepIds.has(quiz.step_id);
}

export function TeachingViewDialog({ design, open, onClose }: { design: PlayDesign; open: boolean; onClose: () => void }) {
  const { session } = useSession();
  const dialogRef = useRef<HTMLElement>(null);
  const initialRef = useRef<HTMLSelectElement>(null);
  const roles = useMemo(() => {
    const values = (design.players ?? []).flatMap((player) => [player.position, player.role, player.id]).filter((value): value is string => Boolean(value));
    return [...new Set([...values, 'coach'])];
  }, [design.players]);
  const [role, setRole] = useState(roles[0] ?? 'coach');
  const [mode, setMode] = useState<TeachingMode>(roles[0] === 'coach' ? 'coach' : 'player');
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string>('');
  const roleViewQuery = usePlayRoleViewQuery(open && design._revision ? design.id : undefined, role, mode, mode === 'coach' ? undefined : step);
  useModalFocusTrap(open, dialogRef, initialRef, onClose);

  if (!open) return null;

  const view = roleViewQuery.data;
  const steps = view?.steps ?? [];
  const revealedSteps = steps.filter((item) => item.revealed !== false);
  const revealedStepIds = new Set(revealedSteps.map((item) => item.id));
  const quizzes = (view?.quizzes ?? []).filter((quiz) => quizIsVisible(quiz, revealedStepIds));
  const masteredSteps = new Set(view?.mastery.summary.mastered_steps ?? []);
  const canReveal = mode !== 'coach' && step < Math.max(0, steps.length - 1);

  const changeRole = (nextRole: string) => {
    setRole(nextRole);
    setMode(nextRole === 'coach' ? 'coach' : 'player');
    setStep(0);
    setFeedback({});
  };

  const changeMode = (nextMode: TeachingMode) => {
    setMode(nextMode);
    setStep(0);
    setFeedback({});
  };

  const markMastered = async (stepId: string) => {
    if (!session) return;
    setBusy(`mastery:${stepId}`);
    try {
      await recordPlayMastery(session, { designId: design.id, role, stepId, score: 1, result: 'mastered' });
      setFeedback((current) => ({ ...current, [stepId]: 'Marked mastered and linked to the learner record.' }));
    } catch (failure) {
      setFeedback((current) => ({ ...current, [stepId]: failure instanceof Error ? failure.message : 'Mastery could not be recorded.' }));
    } finally {
      setBusy('');
    }
  };

  const submitQuizAnswer = async (quiz: PlayRoleViewQuiz) => {
    if (!session || answers[quiz.id] === undefined) return;
    setBusy(`quiz:${quiz.id}`);
    try {
      const result = await submitPlayQuiz(session, { designId: design.id, role, quizId: quiz.id, answer: answers[quiz.id] });
      setFeedback((current) => ({ ...current, [quiz.id]: result.correct ? 'Correct — mastery recorded.' : 'Needs review — revisit the assignment and try again.' }));
    } catch (failure) {
      setFeedback((current) => ({ ...current, [quiz.id]: failure instanceof Error ? failure.message : 'Quiz response could not be recorded.' }));
    } finally {
      setBusy('');
    }
  };

  return createPortal(
    <div className="modal-backdrop designer-modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="designer-export-dialog" style={{ width: 'min(760px, calc(100vw - 2rem))', maxHeight: 'calc(100dvh - 2rem)', overflowY: 'auto' }} role="dialog" aria-modal="true" aria-labelledby="teaching-view-title">
        <button className="designer-dialog-close" type="button" aria-label="Close teaching view" onClick={onClose}><X size={18} /></button>
        <span className="designer-dialog-icon"><GraduationCap size={22} /></span>
        <p className="designer-kicker">Role-based learning surface</p>
        <h2 id="teaching-view-title">Teach {design.name || design.concept || design.id}</h2>
        <p>Reveal only the assignment, timing, coaching cue, and checks that this learner or staff role needs. Every quiz and mastery action is recorded against the canonical play.</p>
        <div className="export-dialog-grid">
          <label><span>Role or position group</span><select ref={initialRef} value={role} onChange={(event) => changeRole(event.target.value)}>{roles.map((value) => <option value={value} key={value}>{value.replaceAll('_', ' ')}</option>)}</select></label>
          <label><span>Teaching mode</span><select value={mode} onChange={(event) => changeMode(event.target.value as TeachingMode)}><option value="player">Player view</option><option value="position_group">Position-group view</option><option value="coach">Coach / staff view</option></select></label>
        </div>
        {!design._revision ? <p className="review-warning" role="status">Save this play first. Teaching views are generated from the organization’s immutable server revision.</p> : null}
        {roleViewQuery.isPending ? <p className="export-result" role="status"><LoaderCircle className="spin" size={18} /> Loading the filtered teaching view…</p> : null}
        {roleViewQuery.isError ? <p className="export-error" role="alert">{roleViewQuery.error instanceof Error ? roleViewQuery.error.message : 'Teaching view could not be loaded.'}</p> : null}
        {view ? (
          <>
            <div className="export-result" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
              <span><strong>{revealedSteps.length}/{steps.length || 0}</strong><small> steps visible</small></span>
              <span><strong>{view.mastery.summary.mastered_step_count ?? 0}</strong><small> mastered</small></span>
              <span><strong>{String(view.filtered_diagram?.hidden_element_count ?? 0)}</strong><small> elements hidden</small></span>
            </div>
            <TeachingDiagram view={view} stepIndex={mode === 'coach' ? Math.max(0, steps.length - 1) : step} onStepChange={setStep} />
            <div className="inspector-help" style={{ marginBottom: '0.8rem' }}><strong>Accessible read-through</strong><p style={{ whiteSpace: 'pre-line' }}>{view.accessible_text || 'No accessible assignment text is available yet.'}</p></div>
            <div className="export-dialog-grid" style={{ gridTemplateColumns: '1fr auto', alignItems: 'end' }}>
              <label><span>Teaching progress</span><progress max={Math.max(1, steps.length)} value={revealedSteps.length} /></label>
              <button className="button button--secondary" type="button" disabled={!canReveal} onClick={() => setStep((current) => Math.min(current + 1, Math.max(0, steps.length - 1)))}>{canReveal ? 'Reveal next step' : mode === 'coach' ? 'All steps visible' : 'All steps revealed'}</button>
            </div>
            <div className="version-list" aria-label="Revealed assignment steps">
              {revealedSteps.length ? revealedSteps.map((item) => <article className="version-list__item" key={item.id} style={{ display: 'grid', gap: '0.35rem' }}><div><strong>{(item.step_index ?? 0) + 1}. {item.label || 'Assignment step'}</strong><small>{item.start_ms ?? 0}–{item.end_ms ?? 0} ms</small></div><p>{item.instruction || 'Execute the assigned path and coaching cue.'}</p>{item.gap_owner || item.exchange_with || item.replacement_zone ? <div className="teaching-responsibility-chips" aria-label="Defensive responsibility context">{item.gap_owner ? <span>Gap: {item.gap_owner}</span> : null}{item.exchange_with ? <span>Exchange: {item.exchange_role?.replaceAll('_', ' ') || 'exchange'} ↔ {item.exchange_with}</span> : null}{item.replacement_zone ? <span>Replace: {item.replacement_zone}</span> : null}{item.rotation_trigger ? <span>Trigger: {item.rotation_trigger.replaceAll('_', ' ')}</span> : null}</div> : null}<div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', flexWrap: 'wrap' }}><button className="button button--secondary" type="button" disabled={busy === `mastery:${item.id}` || masteredSteps.has(item.id)} onClick={() => void markMastered(item.id)}>{busy === `mastery:${item.id}` ? <LoaderCircle className="spin" size={14} /> : <CheckCircle2 size={14} />} {item.mastered || masteredSteps.has(item.id) ? 'Mastered' : 'Mark mastered'}</button>{item.mastered ? <span className="teaching-mastery-state">Phase mastered</span> : null}{feedback[item.id] ? <span role="status">{feedback[item.id]}</span> : null}</div></article>) : <p className="review-warning">No authored steps are available for this role yet. Add player-linked assignments and timing phases in the editor.</p>}
            </div>
            {quizzes.length ? <div className="comment-list" style={{ marginTop: '0.9rem' }}><h3><MessageCircleQuestion size={16} /> Knowledge checks</h3>{quizzes.map((quiz) => <article className="comment-list__item" key={quiz.id}><strong>{quiz.question || 'What is your assignment?'}</strong>{quiz.options?.length ? <div style={{ display: 'grid', gap: '0.35rem', marginTop: '0.5rem' }}>{quiz.options.map((option, index) => { const value = String(optionValue(option) ?? ''); return <label key={`${quiz.id}-${index}`} style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}><input type="radio" name={`quiz-${quiz.id}`} value={value} checked={answers[quiz.id] === value} onChange={(event) => setAnswers((current) => ({ ...current, [quiz.id]: event.target.value }))} /> <span>{optionLabel(option)}</span></label>; })}</div> : <input aria-label={`Answer for ${quiz.question || quiz.id}`} value={answers[quiz.id] ?? ''} onChange={(event) => setAnswers((current) => ({ ...current, [quiz.id]: event.target.value }))} /> }<button className="button button--secondary" type="button" disabled={busy === `quiz:${quiz.id}` || answers[quiz.id] === undefined || answers[quiz.id] === ''} onClick={() => void submitQuizAnswer(quiz)}>{busy === `quiz:${quiz.id}` ? <LoaderCircle className="spin" size={14} /> : <CheckCircle2 size={14} />} Check answer</button>{feedback[quiz.id] ? <span role="status">{feedback[quiz.id]}</span> : null}</article>)}</div> : null}
            {view.practice_linkage && Object.values(view.practice_linkage).some((value) => Array.isArray(value) ? value.length : Boolean(value)) ? <div className="inspector-help" style={{ marginTop: '0.9rem' }}><strong>Practice linkage</strong><p>{Object.entries(view.practice_linkage).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${Array.isArray(value) ? value.join(', ') || 'none' : String(value)}`).join(' · ')}</p></div> : null}
            {mode === 'coach' && view.coaching_notes?.length ? <div className="inspector-help" style={{ marginTop: '0.9rem' }}><strong>Staff coaching notes</strong><ul>{view.coaching_notes.map((note, index) => <li key={`${index}-${note}`}>{note}</li>)}</ul></div> : null}
          </>
        ) : null}
      </section>
    </div>,
    document.body,
  );
}
