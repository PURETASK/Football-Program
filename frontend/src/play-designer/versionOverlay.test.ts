import { describe, expect, it } from 'vitest';
import { versionChangeLabel, versionOverlayChanges } from './versionOverlay';

describe('version overlay changes', () => {
  it('classifies added, changed, unchanged, and removed field objects', () => {
    const result = versionOverlayChanges({
      elements: [{ id: 'A', kind: 'route', points: [{ x: 1, y: 2 }] }, { id: 'B', kind: 'block', assignment: 'pull' }],
      players: [{ id: 'P1', position: 'QB' }, { id: 'P3', position: 'WR' }],
    }, {
      elements: [{ id: 'A', kind: 'route', points: [{ x: 1, y: 2 }] }, { id: 'B', kind: 'block', assignment: 'base' }, { id: 'C', kind: 'route' }],
      players: [{ id: 'P1', position: 'QB' }, { id: 'P2', position: 'RB' }],
    });
    expect(result.elements.get('A')).toBe('unchanged');
    expect(result.elements.get('B')).toBe('changed');
    expect(result.elements.has('C')).toBe(false);
    expect(result.removedElements).toEqual(new Set(['C']));
    expect(result.players.get('P3')).toBe('added');
    expect(result.removedPlayers).toEqual(new Set(['P2']));
  });

  it('uses stable object-key ordering and explainable labels', () => {
    const result = versionOverlayChanges({ elements: [{ id: 'A', kind: 'route', points: [{ x: 1, y: 2 }], note: 'same' }] }, { elements: [{ note: 'same', points: [{ y: 2, x: 1 }], kind: 'route', id: 'A' }] });
    expect(result.elements.get('A')).toBe('unchanged');
    expect(versionChangeLabel('changed')).toBe('changed from compared version');
  });
});
