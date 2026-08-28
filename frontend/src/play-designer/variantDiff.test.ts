import { describe, expect, it } from 'vitest';
import type { PlayDesign } from '../types';
import { diffPlayVariant } from './variantDiff';

const SOURCE: PlayDesign = { id: 'SOURCE', unit: 'offense', formation: 'trips', coverage: 'cover_3', elements: [
  { id: 'ROUTE-X', kind: 'route', type: 'go', points: [{ x: 10, y: 30 }, { x: 10, y: 10 }] },
  { id: 'ROUTE-Y', kind: 'route', type: 'dig', points: [{ x: 20, y: 30 }, { x: 20, y: 10 }] },
] };

describe('variant diff', () => {
  it('reports metadata, assignment changes, additions, removals, and stable elements', () => {
    const variant: PlayDesign = { ...SOURCE, id: 'VARIANT', coverage: 'quarters', elements: [
      { ...SOURCE.elements![0], type: 'post' },
      { id: 'ROUTE-Z', kind: 'route', type: 'out', points: [{ x: 30, y: 30 }, { x: 40, y: 20 }] },
    ] };
    expect(diffPlayVariant(SOURCE, variant)).toEqual({ metadata: ['coverage'], elements: { added: ['ROUTE-Z'], removed: ['ROUTE-Y'], changed: [{ id: 'ROUTE-X', fields: ['type'] }] }, unchanged_elements: 0 });
  });
});
