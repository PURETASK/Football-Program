import type { PlayDesign, PlayElement, ValidationIssue } from '../types';
import { timelineEventKind } from './timelineEvents';

const REPLACEMENT_ROLES = new Set(['rush_replace', 'drop_replace', 'rotate_replace']);
const RUSH_KINDS = new Set(['rush', 'stunt']);
const COVERAGE_KINDS = new Set(['coverage', 'rotation']);
const EXCHANGE_EVENT_KINDS = new Set(['exchange', 'rotation', 'block_exchange', 'rush_exchange']);

function issue(code: string, message: string, path: string, suggestion: string, severity: ValidationIssue['severity'] = 'warning'): ValidationIssue {
  return { code, message, path, suggestion, severity, overrideable: true };
}

export function defensiveResponsibilityIssues(design: PlayDesign): ValidationIssue[] {
  if (design.unit !== 'defense') return [];
  const elements = design.elements ?? [];
  const indexOf = (id: string) => elements.findIndex((element) => element.id === id);
  const findings: ValidationIssue[] = [];
  const seenPairs = new Set<string>();
  const seenSequence = new Map<number, number>();
  const timelineEvents = design.timeline?.events ?? [];

  elements.forEach((element, index) => {
    if (element.exchange_with) {
      const partnerIndex = indexOf(element.exchange_with);
      const partner = partnerIndex >= 0 ? elements[partnerIndex] : undefined;
      if (!partner) findings.push(issue('EXCHANGE_PARTNER_MISSING', `Exchange partner ${element.exchange_with} does not exist in this design.`, `elements[${index}].exchange_with`, 'Select an existing assignment or clear the exchange.', 'error'));
      else {
        const pairKey = [element.id, partner.id].sort().join('::');
        if (!seenPairs.has(pairKey)) {
          seenPairs.add(pairKey);
          if (partner.exchange_with !== element.id) findings.push(issue('EXCHANGE_NOT_RECIPROCAL', `${element.id} names ${partner.id}, but the partner does not point back.`, `elements[${index}].exchange_with`, 'Create or repair the reciprocal exchange pair.', 'error'));
          const role = element.exchange_role ?? '';
          if (role === 'rush_replace' && (!RUSH_KINDS.has(element.kind) || !COVERAGE_KINDS.has(partner.kind))) findings.push(issue('EXCHANGE_ROLE_MISMATCH', 'Rush → replace expects a rush-side assignment paired with a coverage replacement.', `elements[${index}].exchange_role`, 'Use a rush/stunt assignment with a coverage or rotation partner.'));
          if (role === 'drop_replace' && (!COVERAGE_KINDS.has(element.kind) || !RUSH_KINDS.has(partner.kind))) findings.push(issue('EXCHANGE_ROLE_MISMATCH', 'Drop → replace expects a coverage-side assignment paired with a rush replacement.', `elements[${index}].exchange_role`, 'Use a coverage/rotation assignment with a rush/stunt partner.'));
          if (REPLACEMENT_ROLES.has(role) && !partner.rotation_to_zone && !partner.zone) findings.push(issue('REPLACEMENT_OWNER_MISSING', `The ${role.replace('_', ' ')} exchange has no replacement zone on ${partner.id}.`, `elements[${partnerIndex}].rotation_to_zone`, 'Assign the partner’s replacement zone before approval.', 'error'));
          if (!timelineEvents.some((event) => EXCHANGE_EVENT_KINDS.has(timelineEventKind(event)) && (event.element_id === element.id || event.element_id === partner.id))) findings.push(issue('EXCHANGE_TIMELINE_MISSING', `The ${element.id} ↔ ${partner.id} exchange has no synchronized exchange or rotation timeline cue.`, `elements[${index}].exchange_with`, 'Add an Exchange, Block exchange, Rush exchange, or Rotation cue at the post-snap trigger.', 'warning'));
        }
      }
    }
    if (element.rotation_sequence !== undefined) {
      const previous = seenSequence.get(element.rotation_sequence);
      if (previous !== undefined) findings.push(issue('ROTATION_SEQUENCE_DUPLICATE', `Rotation sequence ${element.rotation_sequence} is also used by elements[${previous}].`, `elements[${index}].rotation_sequence`, 'Give each post-snap rotation step a unique sequence number.'));
      else seenSequence.set(element.rotation_sequence, index);
      if (!timelineEvents.some((event) => EXCHANGE_EVENT_KINDS.has(timelineEventKind(event)) && event.element_id === element.id)) findings.push(issue('ROTATION_TIMELINE_MISSING', `${element.id} has a rotation sequence but no synchronized timeline cue.`, `elements[${index}].rotation_sequence`, 'Add a Rotation, Exchange, Block exchange, or Rush exchange cue and attach it to this assignment.', 'warning'));
      if (!element.rotation_trigger) findings.push(issue('ROTATION_TRIGGER_MISSING', `${element.id} has a sequence order but no post-snap trigger.`, `elements[${index}].rotation_trigger`, 'Choose the football event that starts this rotation step.', 'warning'));
      if (!Number.isInteger(element.rotation_sequence) || element.rotation_sequence < 1) findings.push(issue('ROTATION_SEQUENCE_INVALID', `${element.id} has an invalid rotation sequence number.`, `elements[${index}].rotation_sequence`, 'Use a positive whole-number sequence order.', 'error'));
    }
    if (element.kind === 'rotation' && element.rotation_replacement_player_id && !(design.players ?? []).some((player) => player.id === element.rotation_replacement_player_id)) {
      findings.push(issue('ROTATION_REPLACEMENT_PLAYER_MISSING', `${element.id} names replacement player ${element.rotation_replacement_player_id}, but that player is not in the design.`, `elements[${index}].rotation_replacement_player_id`, 'Choose a player from this defensive design or clear the replacement field.', 'error'));
    }
    if (element.kind === 'rotation' && (element.rotation_to_zone || element.zone) && !element.rotation_vacated_zone) {
      findings.push(issue('ROTATION_VACATED_ZONE_MISSING', `${element.id} has a replacement destination but does not document the vacated responsibility.`, `elements[${index}].rotation_vacated_zone`, 'Name the zone or responsibility left by the rotating defender.', 'warning'));
    }
  });

  for (const zone of design.coverage_zones ?? []) {
    const owners = elements.filter((element) => element.zone === zone || element.rotation_to_zone === zone);
    if (!owners.length) findings.push(issue('SHELL_ZONE_UNOWNED', `Declared shell zone ${zone} has no coverage or replacement assignment owner.`, 'coverage_zones', 'Add an assignment to the zone or remove the declaration.', 'error'));
    else if (owners.length > 1) findings.push(issue('SHELL_ZONE_MULTI_OWNER', `Declared shell zone ${zone} has multiple assignment owners: ${owners.map((element) => element.player_id ?? element.type ?? element.id).join(', ')}.`, 'coverage_zones', 'Confirm whether this is a deliberate bracket/rotation; otherwise assign one canonical owner.', 'warning'));
  }

  const gaps = new Map<string, PlayElement[]>();
  for (const element of elements) {
    if (!element.gap_owner) continue;
    const owners = gaps.get(element.gap_owner) ?? [];
    owners.push(element);
    gaps.set(element.gap_owner, owners);
  }
  for (const [gap, owners] of gaps) {
    if (owners.length > 1) findings.push(issue('GAP_OWNERSHIP_CONFLICT', `Gap ${gap} has multiple fit owners: ${owners.map((element) => element.player_id ?? element.type ?? element.id).join(', ')}.`, 'elements', 'Resolve the duplicate fit, or document the exchange/lever rule that makes the shared ownership intentional.', 'warning'));
  }
  return findings;
}
