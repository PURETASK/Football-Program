import type { PlayDesign, PlayElement, PlayTimelineEvent, ValidationIssue } from '../types';
import { timelineEventEnd, timelineEventKind, timelineEventStart } from './timelineEvents';
import { elementTiming } from './timelineModel';

function finding(code: string, message: string, path: string, suggestion: string, severity: ValidationIssue['severity'] = 'error'): ValidationIssue {
  return { code, message, path, suggestion, severity, overrideable: false };
}

function finite(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function branchIds(element: PlayElement): Set<string> {
  return new Set((element.branches ?? []).map((branch) => branch.id).filter(Boolean));
}

function validateEvent(event: PlayTimelineEvent, index: number, design: PlayDesign, duration: number): ValidationIssue[] {
  const start = timelineEventStart(event);
  const end = timelineEventEnd(event, duration);
  const declaredEnd = event.end_ms === undefined ? end : Number(event.end_ms);
  const path = `timeline.events[${index}]`;
  const issues: ValidationIssue[] = [];
  if (!finite(start) || !finite(end)) {
    issues.push(finding('TIMELINE_WINDOW_NOT_NUMERIC', `Timeline event ${event.label ?? timelineEventKind(event)} has a non-numeric time window.`, path, 'Enter finite millisecond values for the event start and end.'));
  } else {
    if (start < 0) issues.push(finding('TIMELINE_START_BEFORE_SNAP', `Timeline event ${event.label ?? timelineEventKind(event)} starts before the snap clock.`, `${path}.start_ms`, 'Use zero or a deliberate pre-snap value only when the event is explicitly modeled as pre-snap.', 'warning'));
    if (!finite(declaredEnd) || declaredEnd <= start) issues.push(finding('TIMELINE_WINDOW_INVALID', `Timeline event ${event.label ?? timelineEventKind(event)} ends at or before it starts.`, `${path}.end_ms`, 'Set the end time after the start time.'));
    if (end > duration) issues.push(finding('TIMELINE_END_OUT_OF_RANGE', `Timeline event ${event.label ?? timelineEventKind(event)} ends after the ${duration} ms play clock.`, `${path}.end_ms`, 'Extend the play duration or move the event inside the play clock.'));
  }

  if (event.element_id) {
    const elementIndex = (design.elements ?? []).findIndex((element) => element.id === event.element_id);
    if (elementIndex < 0) issues.push(finding('TIMELINE_ELEMENT_MISSING', `Timeline event ${event.label ?? timelineEventKind(event)} references missing assignment ${event.element_id}.`, `${path}.element_id`, 'Select an existing assignment or remove the stale event reference.'));
    else if (event.branch_id && !branchIds(design.elements![elementIndex]).has(event.branch_id)) issues.push(finding('TIMELINE_BRANCH_MISSING', `Timeline event ${event.label ?? timelineEventKind(event)} references branch ${event.branch_id}, which is not on assignment ${event.element_id}.`, `${path}.branch_id`, 'Choose a branch from the attached route or attach the cue to the primary path.'));
  }
  if (event.player_id && !(design.players ?? []).some((player) => player.id === event.player_id)) issues.push(finding('TIMELINE_PLAYER_MISSING', `Timeline event ${event.label ?? timelineEventKind(event)} references missing player ${event.player_id}.`, `${path}.player_id`, 'Choose a player in this design or clear the player reference.'));
  return issues;
}

function validateElementTiming(element: PlayElement, index: number, duration: number): ValidationIssue[] {
  const timing = elementTiming(element, duration);
  const path = `elements[${index}].timing`;
  const issues: ValidationIssue[] = [];
  if (!finite(timing.start) || !finite(timing.end) || timing.end <= timing.start) issues.push(finding('ELEMENT_TIMING_INVALID', `Assignment ${element.id} has an invalid timing window.`, path, 'Set an end time after the assignment start time.'));
  if (timing.start < 0) issues.push(finding('ELEMENT_START_BEFORE_SNAP', `Assignment ${element.id} starts before the snap clock.`, `${path}.start_ms`, 'Use zero or a documented pre-snap phase.', 'warning'));
  if (timing.end > duration) issues.push(finding('ELEMENT_END_OUT_OF_RANGE', `Assignment ${element.id} ends after the ${duration} ms play clock.`, `${path}.end_ms`, 'Extend the play duration or shorten the assignment window.'));
  const phases = element.timing?.phases ?? [];
  phases.forEach((phase, phaseIndex) => {
    if (!finite(phase.start_ms) || !finite(phase.end_ms) || phase.end_ms <= phase.start_ms) issues.push(finding('TIMELINE_PHASE_INVALID', `Assignment ${element.id} phase ${phase.id} has an invalid window.`, `${path}.phases[${phaseIndex}]`, 'Set each phase end after its start.'));
    if (phase.start_ms < timing.start || phase.end_ms > timing.end) issues.push(finding('TIMELINE_PHASE_OUTSIDE_ASSIGNMENT', `Assignment ${element.id} phase ${phase.id} falls outside its assignment window.`, `${path}.phases[${phaseIndex}]`, 'Keep every phase inside the assignment start and end times.', 'warning'));
  });
  const sorted = [...phases].sort((left, right) => left.start_ms - right.start_ms);
  sorted.slice(1).forEach((phase, phaseIndex) => {
    const previous = sorted[phaseIndex];
    if (phase.start_ms < previous.end_ms) issues.push(finding('TIMELINE_PHASE_OVERLAP', `Assignment ${element.id} phases ${previous.id} and ${phase.id} overlap.`, path, 'Adjust phase windows so one phase completes before the next begins.', 'warning'));
  });
  return issues;
}

function validatePreSnapSequence(design: PlayDesign, snapMs: number): ValidationIssue[] {
  const steps = design.pre_snap_sequence ?? [];
  const issues: ValidationIssue[] = [];
  const seenIds = new Map<string, number>();
  let previous: { id: string; start_ms: number; end_ms: number } | undefined;
  steps.forEach((step, index) => {
    const path = `pre_snap_sequence[${index}]`;
    const start = Number(step.start_ms);
    const end = Number(step.end_ms);
    if (!step.id?.trim()) issues.push(finding('PRESNAP_STEP_ID_MISSING', `Pre-snap step ${index + 1} has no stable ID.`, `${path}.id`, 'Give every pre-snap step a unique ID.'));
    else if (seenIds.has(step.id)) issues.push(finding('PRESNAP_STEP_ID_DUPLICATE', `Pre-snap step ID ${step.id} is used more than once.`, `${path}.id`, 'Give every pre-snap step a unique ID.'));
    else seenIds.set(step.id, index);
    if (!step.label?.trim()) issues.push(finding('PRESNAP_LABEL_MISSING', `Pre-snap step ${index + 1} has no coaching label.`, `${path}.label`, 'Name the communication or movement cue so players can understand it.'));
    if (!finite(start) || !finite(end)) {
      issues.push(finding('PRESNAP_WINDOW_NOT_NUMERIC', `Pre-snap step ${step.label || index + 1} has a non-numeric time window.`, path, 'Enter finite millisecond values for the pre-snap step.'));
    } else {
      if (start < -5000) issues.push(finding('PRESNAP_START_OUT_OF_RANGE', `Pre-snap step ${step.label || index + 1} starts before the supported -5,000 ms rehearsal window.`, `${path}.start_ms`, 'Keep the pre-snap step between -5,000 ms and the snap.'));
      if (end <= start) issues.push(finding('PRESNAP_WINDOW_INVALID', `Pre-snap step ${step.label || index + 1} ends at or before it starts.`, `${path}.end_ms`, 'Set the end time after the start time.'));
      if (end > snapMs) issues.push(finding('PRESNAP_END_AFTER_SNAP', `Pre-snap step ${step.label || index + 1} continues after the snap at ${snapMs} ms.`, `${path}.end_ms`, 'End the pre-snap step at or before the snap, or model the post-snap work as an assignment/event.'));
      if (previous) {
        if (start < previous.start_ms) issues.push(finding('PRESNAP_SEQUENCE_OUT_OF_ORDER', `Pre-snap step ${step.label || index + 1} is ordered before ${previous.id} but starts later in the sequence.`, `${path}.start_ms`, 'Reorder the steps chronologically or correct their start times.'));
        if (start < previous.end_ms) issues.push(finding('PRESNAP_STEPS_OVERLAP', `Pre-snap steps ${previous.id} and ${step.id} overlap.`, path, 'Separate the communication windows or document an intentional simultaneous action.'));
      }
      previous = { id: step.id, start_ms: start, end_ms: end };
    }
  });
  return issues;
}

/** Validate editor timeline references and timing before a draft reaches the server. */
export function timelineIntegrityIssues(design: PlayDesign): ValidationIssue[] {
  const duration = Number(design.timeline?.duration_ms ?? 3000);
  const safeDuration = finite(duration) && duration > 0 ? duration : 3000;
  const declaredSnap = Number(design.timeline?.snap_ms ?? 0);
  const snapMs = finite(declaredSnap) ? declaredSnap : 0;
  const issues: ValidationIssue[] = [];
  issues.push(...validatePreSnapSequence(design, snapMs));
  const events = design.timeline?.events ?? [];
  const seenEventIds = new Map<string, number>();
  events.forEach((event, index) => {
    if (event.id) {
      const previous = seenEventIds.get(event.id);
      if (previous !== undefined) issues.push(finding('TIMELINE_EVENT_ID_DUPLICATE', `Timeline event ID ${event.id} is used by events ${previous + 1} and ${index + 1}.`, `timeline.events[${index}].id`, 'Give every synchronized event a unique ID.'));
      else seenEventIds.set(event.id, index);
    }
    issues.push(...validateEvent(event, index, design, safeDuration));
  });
  (design.elements ?? []).forEach((element, index) => issues.push(...validateElementTiming(element, index, safeDuration)));
  return issues;
}
