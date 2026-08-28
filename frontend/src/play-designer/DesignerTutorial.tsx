import { ArrowLeft, ArrowRight, BookOpenCheck, Check, CircleHelp, X } from 'lucide-react';
import { useEffect, useRef, type KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';

export type TutorialTarget = 'toolbar' | 'assets' | 'canvas' | 'timeline' | 'inspector' | 'review';

export interface TutorialStep {
  id: string;
  target: TutorialTarget;
  eyebrow: string;
  title: string;
  description: string;
  details: string[];
  tryThis?: string;
}

export const DESIGNER_TUTORIAL_STEPS: TutorialStep[] = [
  {
    id: 'welcome', target: 'toolbar', eyebrow: 'Welcome', title: 'Build one canonical football call',
    description: 'The Play Designer keeps the diagram, football intent, timing, validation, staff decisions, teaching views, and outputs connected to one structured play record.',
    details: ['The organization-scoped Python API remains canonical.', 'Every visible object can carry football and teaching metadata.', 'Autosave, review, publishing, and overrides preserve human control.', 'Nothing in this tutorial changes the play by itself.'],
  },
  {
    id: 'assets', target: 'assets', eyebrow: 'Step 1', title: 'Start from the intelligent asset library',
    description: 'Search formations, routes, motions, runs, protections, fronts, coverages, pressures, checks, landmarks, and teaching annotations without redrawing common football language.',
    details: ['Use category, unit, lifecycle, and compatible-only filters.', 'Compatibility is scored against formation, personnel, and rule profile.', 'Formation and front thumbnails show the actual 11-player spacing.', 'Deprecated assets identify their approved replacement.'],
    tryThis: 'Search for Post, inspect its compatibility reasons, choose it, then drag from a receiver on the field.',
  },
  {
    id: 'alignment', target: 'inspector', eyebrow: 'Step 2', title: 'Establish formation and field context',
    description: 'Set personnel, formation or front, hash, line of scrimmage, strength, direction, and field zone before adding assignments.',
    details: ['A formation or front preset applies stable role-based alignment slots.', 'Hash and line changes translate every unlocked object together.', 'Locked objects remain fixed as deliberate exceptions.', 'The same normalized field drives animation, teaching views, and exports.'],
    tryThis: 'Change the ball from the middle to the right hash, then apply a formation preset and verify the whole call moves together.',
  },
  {
    id: 'canvas', target: 'canvas', eyebrow: 'Step 3', title: 'Author precisely on the field',
    description: 'Use the shared 100-by-53 coordinate field to draw and edit routes, motion, runs, blocks, coverage, rushes, stunts, fits, rotations, and annotations.',
    details: ['Drag a path tool from its player to author an assignment.', 'Double-click a path to add a handle; use Delete on a handle to remove it.', 'Marquee or Shift-click to build a multi-selection.', 'Drag players and their linked assignments together; arrow keys provide precise nudging.'],
    tryThis: 'Select a route handle and use Alt plus an arrow key for fine movement, or Shift plus an arrow key for a five-yard adjustment.',
  },
  {
    id: 'toolbar', target: 'toolbar', eyebrow: 'Step 4', title: 'Control the editing workflow',
    description: 'The toolbar controls authoring mode, history, selection operations, snapping, staff actions, exports, teaching views, and save state.',
    details: ['Undo and redo preserve a bounded local history.', 'Duplicate, group, mirror, lock, and delete operate on the selection.', 'Pan and zoom do not alter football coordinates.', 'Staff presence and connection state remain visible while editing.'],
    tryThis: 'Select two objects, group them, mirror them, then undo and redo the operation.',
  },
  {
    id: 'assignment-graph', target: 'inspector', eyebrow: 'Step 5', title: 'Describe the football assignment, not only the arrow',
    description: 'The structured assignment panel records who owns an action, what it targets, what it keys, what must happen first, and how the responsibility should be taught.',
    details: ['Record objective, technique, landmark, depth, leverage, gap or zone, and read language.', 'Link a target player or target assignment.', 'Add prerequisite and exchange relationships.', 'Mark genuinely exclusive responsibilities so overlaps become explainable conflicts.'],
    tryThis: 'Select a defender, set the back as the read key, add a fit landmark, then make the fit depend on the read assignment.',
  },
  {
    id: 'timeline', target: 'timeline', eyebrow: 'Step 6', title: 'Teach timing on synchronized tracks',
    description: 'Open Tracks to see every assignment on one clock with football-specific phases, markers, deliberate pauses, narration, and ball events.',
    details: ['Use 0.5x through 2x playback or step between cues.', 'Pause markers stop playback for a teaching conversation.', 'Each route, block, rush, fit, read, or rotation carries editable phases.', 'Bind the ball to a selected path and display or speak a synchronized coach cue.'],
    tryThis: 'Add a pause at the route break, add a narration cue, bind the ball to the selected path, then replay at 0.5x.',
  },
  {
    id: 'validation', target: 'inspector', eyebrow: 'Step 7', title: 'Check the unsaved draft live',
    description: 'The Checks tab validates the current draft after edits without persisting it, so issues appear before the next save or review request.',
    details: ['Structural and rule-profile findings identify their exact data path.', 'Assignment checks detect missing targets, stale references, cycles, timing conflicts, and duplicate exclusive responsibilities.', 'Suggested actions explain how to resolve supported findings.', 'Locate on canvas selects the affected player or assignment.'],
    tryThis: 'Create a dependency cycle between two assignments, open Checks, locate the finding, and remove one dependency.',
  },
  {
    id: 'review', target: 'review', eyebrow: 'Step 8', title: 'Save, compare, review, branch, and release',
    description: 'A call becomes operational only after its canonical revision, validation state, human decision reference, immutable snapshot, and output artifact are explicit.',
    details: ['Autosave creates server revisions and encrypted offline recovery data.', 'Visual comparison reports metadata, player, assignment, and timeline changes.', 'Guarded merges preserve the branch base and expose conflicts for human resolution.', 'Publishing, rollback, legality overrides, and exports remain role controlled and auditable.'],
    tryThis: 'Save the draft, compare two snapshots, add an element-linked comment, then request review with a real decision reference.',
  },
  {
    id: 'complete', target: 'canvas', eyebrow: 'Tour complete', title: 'Build, teach, verify, and deliver',
    description: 'Begin with field context, apply an approved formation or front, author structured assignments, synchronize timing, run live checks, save, and request staff review.',
    details: ['Restart this tutorial from the help button at any time.', 'Use player and position-group views to verify comprehension.', 'Generate only validated, approved release outputs for operational use.', 'The Play Designer remains a connected football system, not an isolated drawing board.'],
  },
];

interface DesignerTutorialProps {
  open: boolean;
  stepIndex: number;
  onStep: (index: number) => void;
  onClose: () => void;
  onComplete: () => void;
}

export function DesignerTutorial({ open, stepIndex, onStep, onClose, onComplete }: DesignerTutorialProps) {
  const nextButtonRef = useRef<HTMLButtonElement>(null);
  const step = DESIGNER_TUTORIAL_STEPS[stepIndex] ?? DESIGNER_TUTORIAL_STEPS[0];
  const finalStep = stepIndex === DESIGNER_TUTORIAL_STEPS.length - 1;

  useEffect(() => {
    if (open) nextButtonRef.current?.focus();
  }, [open, stepIndex]);

  if (!open) return null;

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === 'Escape') onClose();
    if (event.key === 'ArrowLeft' && stepIndex > 0) onStep(stepIndex - 1);
    if (event.key === 'ArrowRight' && !finalStep) onStep(stepIndex + 1);
  };

  return createPortal(
    <div className="designer-tutorial-layer" role="presentation">
      <section className="designer-tutorial" role="dialog" aria-modal="false" aria-labelledby="designer-tutorial-title" aria-describedby="designer-tutorial-description" onKeyDown={handleKeyDown}>
        <header>
          <span className="designer-tutorial__mark" aria-hidden="true"><BookOpenCheck size={19} /></span>
          <div><p>{step.eyebrow}</p><strong>Play Designer tutorial</strong></div>
          <button type="button" aria-label="Close tutorial" title="Close tutorial" onClick={onClose}><X size={17} /></button>
        </header>
        <div className="designer-tutorial__progress" aria-label={`Tutorial step ${stepIndex + 1} of ${DESIGNER_TUTORIAL_STEPS.length}`}>
          {DESIGNER_TUTORIAL_STEPS.map((item, index) => (
            <button key={item.id} type="button" className={index === stepIndex ? 'is-active' : index < stepIndex ? 'is-complete' : ''} aria-label={`Go to ${item.title}`} aria-current={index === stepIndex ? 'step' : undefined} onClick={() => onStep(index)}>
              {index < stepIndex ? <Check size={10} /> : index + 1}
            </button>
          ))}
        </div>
        <div className="designer-tutorial__content" aria-live="polite">
          <span><CircleHelp size={14} /> {step.eyebrow}</span>
          <h2 id="designer-tutorial-title">{step.title}</h2>
          <p id="designer-tutorial-description">{step.description}</p>
          <ul>{step.details.map((detail) => <li key={detail}>{detail}</li>)}</ul>
          {step.tryThis ? <div className="designer-tutorial__try"><strong>Try this after the tour</strong><span>{step.tryThis}</span></div> : null}
        </div>
        <footer>
          <button type="button" className="tutorial-secondary" disabled={stepIndex === 0} onClick={() => onStep(stepIndex - 1)}><ArrowLeft size={15} /> Back</button>
          <span>{stepIndex + 1} / {DESIGNER_TUTORIAL_STEPS.length}</span>
          {finalStep ? <button ref={nextButtonRef} type="button" className="tutorial-primary" onClick={onComplete}>Finish tutorial <Check size={15} /></button> : <button ref={nextButtonRef} type="button" className="tutorial-primary" onClick={() => onStep(stepIndex + 1)}>Next <ArrowRight size={15} /></button>}
        </footer>
      </section>
    </div>,
    document.body,
  );
}
