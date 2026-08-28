import type { PlayDesign, PlayElement, ValidationIssue } from '../types';

const REPLACEMENT_ROLES = new Set(['rush_replace', 'drop_replace', 'rotate_replace']);
const RUSH_KINDS = new Set(['rush', 'stunt']);
const COVERAGE_KINDS = new Set(['coverage', 'rotation']);

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
          if (!timelineEvents.some((event) => (event.kind === 'exchange' || event.kind === 'rotation') && (event.element_id === element.id || event.element_id === partner.id))) findings.push(issue('EXCHANGE_TIMELINE_MISSING', `The ${element.id} ↔ ${partner.id} exchange has no synchronized exchange or rotation timeline cue.`, `elements[${index}].exchange_with`, 'Add an Exchange or Rotation cue in the timeline at the post-snap trigger.', 'warning'));
        }
      }
    }
    if (element.rotation_sequence !== undefined) {
      const previous = seenSequence.get(element.rotation_sequence);
      if (previous !== undefined) findings.push(issue('ROTATION_SEQUENCE_DUPLICATE', `Rotation sequence ${element.rotation_sequence} is also used by elements[${previous}].`, `elements[${index}].rotation_sequence`, 'Give each post-snap rotation step a unique sequence number.'));
      else seenSequence.set(element.rotation_sequence, index);
      if (!timelineEvents.some((event) => (event.kind === 'rotation' || event.kind === 'exchange') && event.element_id === element.id)) findings.push(issue('ROTATION_TIMELINE_MISSING', `${element.id} has a rotation sequence but no synchronized timeline cue.`, `elements[${index}].rotation_sequence`, 'Add a Rotation cue and attach it to this assignment.', 'warning'));
    }
  });

  for (const zone of design.coverage_zones ?? []) {
    const owner = elements.find((element) => element.zone === zone || element.rotation_to_zone === zone);
    if (!owner) findings.push(issue('SHELL_ZONE_UNOWNED', `Declared shell zone ${zone} has no coverage or replacement assignment owner.`, 'coverage_zones', 'Add an assignment to the zone or remove the declaration.', 'error'));
  }
  return findings;
}
