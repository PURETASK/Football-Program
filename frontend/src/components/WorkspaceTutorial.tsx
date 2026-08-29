import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpenCheck, Check, CircleHelp, Info, X } from 'lucide-react';
import { createPortal } from 'react-dom';

import { useModalFocusTrap } from '../hooks/useModalFocusTrap';
import type { WorkspaceDefinition } from '../pages/workspaceDefinitions';
import { ALL_WORKSPACE_DEFINITIONS } from '../pages/workspaceDefinitions';

export interface WorkspaceTutorialStep {
  eyebrow: string;
  title: string;
  description: string;
  details: string[];
  tryThis?: string;
}

export interface WorkspaceTutorialModel {
  key: string;
  title: string;
  description: string;
  steps: WorkspaceTutorialStep[];
}

const TODAY_TUTORIAL: WorkspaceTutorialModel = {
  key: 'today',
  title: 'Today command center',
  description: 'Start here when you need to understand what the program should do next.',
  steps: [
    { eyebrow: 'Start here', title: 'Read the program pulse', description: 'Today summarizes readiness, pending work, recent plays, and operational signals without replacing the workspace where the work is completed.', details: ['Use the page as a briefing, not as a substitute for source records.', 'Numbers are organization-scoped when you connect a team.', 'A disconnected page intentionally shows unavailable values instead of invented counts.'], tryThis: 'Connect the synthetic organization, then compare the pending-review count with the Operations Inbox.' },
    { eyebrow: 'Choose a lane', title: 'Follow the next decision', description: 'Each action card points to the individual system that owns the next step.', details: ['Open Playbook to author or review a call.', 'Open Film to inspect evidence.', 'Open Practice to install and measure it.', 'Open Game Plan to assemble the weekly decision.'], tryThis: 'Open the Playbook from the hero, then return with the sidebar.' },
    { eyebrow: 'Close the loop', title: 'Teach, deliver, learn', description: 'The operating system connects play decisions to players, practice, outcomes, and delivery.', details: ['Player learning turns approved content into role-scoped work.', 'Analytics records intended versus actual outcomes.', 'Delivery and Inbox surface ownership, deadlines, and blockers.'], tryThis: 'Use the sidebar to visit Player, Analytics, and Delivery in that order.' },
  ],
};

const PLAYBOOK_TUTORIAL: WorkspaceTutorialModel = {
  key: 'playbook',
  title: 'Playbook library',
  description: 'Use Playbook as the source library for canonical offensive, defensive, and special-teams designs.',
  steps: [
    { eyebrow: 'Library', title: 'Find the right call', description: 'Search and filter the visual library before opening an individual design.', details: ['Search by concept, formation, personnel, or play ID.', 'Filter by offense, defense, or special teams.', 'Filter by draft, review, or published status.', 'Switch between grid and list views depending on whether you are scanning or comparing.'], tryThis: 'Search for “Dagger”, then filter to published offense.' },
    { eyebrow: 'Create', title: 'Start from a governed template', description: 'Templates give you a structured starting point while preserving a new editable design identity.', details: ['Choose an offense or defense entry point.', 'Use registry-backed assets and templates when possible.', 'A template is a starting structure, not an automatic approval.', 'Every new design continues through validation, review, versioning, and export.'], tryThis: 'Choose a template card and inspect the new designer before saving.' },
    { eyebrow: 'Operate', title: 'Open the owning workspace', description: 'A play card is a doorway into the complete Play Designer, teaching, review, and release workflow.', details: ['Open a card to edit the canonical design.', 'Use the dedicated designer for assignments, timeline, legality, and collaboration.', 'Use role-filtered teaching views for player or position-group delivery.', 'Use release outputs only after the required review gates are satisfied.'], tryThis: 'Open PD-DEMO-OFF-DAGGER, then use the Tutorial button inside Play Designer.' },
  ],
};

function modelFromDefinition(definition: WorkspaceDefinition): WorkspaceTutorialModel {
  return {
    key: definition.slug,
    title: definition.title,
    description: definition.description,
    steps: [
      { eyebrow: 'Purpose', title: `What ${definition.title} is for`, description: definition.description, details: [definition.howItWorks, `Used by: ${definition.audience}`, `Produces: ${definition.outcome}`], tryThis: `Start by locating the ${definition.features[0]?.title.toLowerCase() ?? 'first feature'} section on this page.` },
      ...definition.features.map((feature, index) => ({ eyebrow: `Feature ${index + 1} of ${definition.features.length}`, title: feature.title, description: feature.description, details: [feature.howItWorks, `Uses: ${feature.input}`, `Produces: ${feature.output}`, `Control state: ${feature.status}`], tryThis: `Find “${feature.title}” on the page and inspect its current status.` })),
      { eyebrow: 'Workflow', title: 'Run the system in order', description: `Use this sequence when moving work through ${definition.title}.`, details: definition.workflow.map((step) => `${step.title}: ${step.description}`), tryThis: `Begin with “${definition.workflow[0]?.title ?? 'the first step'}”, then confirm the owner and source before moving forward.` },
      { eyebrow: 'Safety', title: 'Know the authority boundary', description: 'The application keeps high-impact football and organizational decisions explicit and reviewable.', details: [definition.boundary, 'Source records remain organization-scoped.', 'Approval, publishing, player status, and external-provider actions stay in their governed workflows.'], tryThis: 'Before taking an action, read the page description and the authority note at the bottom of the workspace.' },
    ],
  };
}

export const WORKSPACE_TUTORIALS: Record<string, WorkspaceTutorialModel> = {
  today: TODAY_TUTORIAL,
  playbook: PLAYBOOK_TUTORIAL,
  ...Object.fromEntries(ALL_WORKSPACE_DEFINITIONS.map((definition) => [definition.slug, modelFromDefinition(definition)])),
};

export function tutorialForPath(pathname: string): WorkspaceTutorialModel | undefined {
  if (pathname === '/' || pathname === '') return WORKSPACE_TUTORIALS.today;
  if (pathname.startsWith('/playbook/designer')) return undefined;
  if (pathname.startsWith('/admin')) return WORKSPACE_TUTORIALS.admin;
  const key = pathname.split('/').filter(Boolean)[0] ?? '';
  return WORKSPACE_TUTORIALS[key] ?? WORKSPACE_TUTORIALS.playbook;
}

export function WorkspaceTutorial({ model, open, onClose }: { model: WorkspaceTutorialModel; open: boolean; onClose: () => void }) {
  const [stepIndex, setStepIndex] = useState(0);
  const dialogRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const step = model.steps[stepIndex] ?? model.steps[0];
  const finalStep = stepIndex === model.steps.length - 1;
  const progress = useMemo(() => `${stepIndex + 1} of ${model.steps.length}`, [model.steps.length, stepIndex]);
  useModalFocusTrap(open, dialogRef, closeButtonRef, onClose);

  useEffect(() => { if (open) setStepIndex(0); }, [model.key, open]);
  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'ArrowRight' && !finalStep) setStepIndex((value) => Math.min(model.steps.length - 1, value + 1));
      if (event.key === 'ArrowLeft') setStepIndex((value) => Math.max(0, value - 1));
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [finalStep, model.steps.length, onClose, open]);

  if (!open || !step) return null;
  return createPortal(
    <div className="modal-backdrop workspace-tutorial-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="workspace-tutorial" role="dialog" aria-modal="true" aria-labelledby="workspace-tutorial-title" aria-describedby="workspace-tutorial-description">
        <header className="workspace-tutorial__header">
          <span className="workspace-tutorial__icon" aria-hidden="true"><BookOpenCheck size={21} /></span>
          <div><p>Workspace tutorial</p><strong>{model.title}</strong></div>
          <button ref={closeButtonRef} className="icon-button" type="button" aria-label="Close workspace tutorial" onClick={onClose}><X size={18} /></button>
        </header>
        <div className="workspace-tutorial__intro"><CircleHelp size={15} /><span>{model.description}</span></div>
        <nav className="workspace-tutorial__progress" aria-label={`Tutorial progress, step ${progress}`}>
          {model.steps.map((item, index) => <button key={`${model.key}-${index}`} type="button" aria-label={`Go to tutorial step ${index + 1}: ${item.title}`} aria-current={index === stepIndex ? 'step' : undefined} className={index === stepIndex ? 'is-active' : index < stepIndex ? 'is-complete' : ''} onClick={() => setStepIndex(index)}>{index < stepIndex ? <Check size={12} /> : index + 1}</button>)}
        </nav>
        <article className="workspace-tutorial__content" aria-live="polite">
          <p className="workspace-tutorial__eyebrow">{step.eyebrow}</p>
          <h2 id="workspace-tutorial-title">{step.title}</h2>
          <p id="workspace-tutorial-description">{step.description}</p>
          <ul>{step.details.map((detail) => <li key={detail}>{detail}</li>)}</ul>
          {step.tryThis ? <div className="workspace-tutorial__try"><Info size={15} /><div><strong>Try this</strong><span>{step.tryThis}</span></div></div> : null}
        </article>
        <footer className="workspace-tutorial__footer">
          <button className="tutorial-secondary" type="button" disabled={stepIndex === 0} onClick={() => setStepIndex((value) => Math.max(0, value - 1))}><ArrowLeft size={15} /> Back</button>
          <span>{progress}</span>
          {finalStep ? <button className="tutorial-primary" type="button" onClick={onClose}>Finish <Check size={15} /></button> : <button className="tutorial-primary" type="button" onClick={() => setStepIndex((value) => Math.min(model.steps.length - 1, value + 1))}>Next <ArrowRight size={15} /></button>}
        </footer>
      </section>
    </div>,
    document.body,
  );
}
