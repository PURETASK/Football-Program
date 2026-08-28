import type { PlayDesign, PlayElement } from '../types';

export interface VariantElementDiff {
  added: string[];
  removed: string[];
  changed: Array<{ id: string; fields: string[] }>;
}

export interface VariantDiff {
  metadata: string[];
  elements: VariantElementDiff;
  unchanged_elements: number;
}

function equal(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function elementFields(before: PlayElement, after: PlayElement): string[] {
  const fields = new Set([...Object.keys(before), ...Object.keys(after)]);
  fields.delete('id');
  return [...fields].filter((field) => !equal(before[field], after[field])).sort();
}

export function diffPlayVariant(source: PlayDesign, variant: PlayDesign): VariantDiff {
  const metadataFields = ['formation', 'front', 'coverage', 'personnel', 'concept', 'rule_profile'];
  const metadata = metadataFields.filter((field) => !equal(source[field], variant[field]));
  const sourceElements = new Map((source.elements ?? []).map((element) => [element.id, element]));
  const variantElements = new Map((variant.elements ?? []).map((element) => [element.id, element]));
  const added = [...variantElements.keys()].filter((id) => !sourceElements.has(id)).sort();
  const removed = [...sourceElements.keys()].filter((id) => !variantElements.has(id)).sort();
  const changed = [...variantElements.keys()].filter((id) => sourceElements.has(id)).map((id) => ({ id, fields: elementFields(sourceElements.get(id)!, variantElements.get(id)!) })).filter((item) => item.fields.length).sort((left, right) => left.id.localeCompare(right.id));
  return { metadata, elements: { added, removed, changed }, unchanged_elements: Math.max(0, (variant.elements ?? []).length - added.length - changed.length) };
}
