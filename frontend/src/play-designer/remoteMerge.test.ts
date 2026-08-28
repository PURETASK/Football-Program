import type { PlayDesign } from '../types';
import { mergeRemoteDesign } from './remoteMerge';

const BASE: PlayDesign = {
  id: 'PLAY-MERGE',
  name: 'Merge test',
  unit: 'offense',
  formation: 'shotgun_2x2',
  players: [{ id: 'X', position: 'WR', start: { x: 10, y: 30 } }, { id: 'QB', position: 'QB', start: { x: 50, y: 38 } }],
  elements: [{ id: 'ROUTE-X', kind: 'route', type: 'post', player_id: 'X', points: [{ x: 10, y: 30 }, { x: 30, y: 10 }] }],
  _revision: 4,
};

describe('remote design merge', () => {
  it('merges independent player and element changes onto the newer server revision', () => {
    const local = { ...BASE, players: BASE.players?.map((player) => player.id === 'X' ? { ...player, start: { x: 12, y: 31 } } : player) };
    const remote = { ...BASE, elements: [...(BASE.elements ?? []), { id: 'REMOTE-RUN', kind: 'run', type: 'inside', points: [{ x: 50, y: 38 }, { x: 55, y: 25 }] }], _revision: 5 };
    const result = mergeRemoteDesign(BASE, local, remote);
    expect(result.status).toBe('merged');
    expect(result.design?.players?.find((player) => player.id === 'X')?.start).toEqual({ x: 12, y: 31 });
    expect(result.design?.elements).toHaveLength(2);
    expect(result.design?._revision).toBe(5);
  });

  it('reports the exact element path when both sides edit the same object', () => {
    const local = { ...BASE, elements: BASE.elements?.map((element) => ({ ...element, type: 'corner' })) };
    const remote = { ...BASE, elements: BASE.elements?.map((element) => ({ ...element, type: 'dig' })), _revision: 5 };
    const result = mergeRemoteDesign(BASE, local, remote);
    expect(result.status).toBe('conflict');
    expect(result.conflictPaths).toContain('elements.ROUTE-X.type');
  });

  it('merges different fields on the same element', () => {
    const local = { ...BASE, elements: BASE.elements?.map((element) => ({ ...element, note: 'Alert the safety' })) };
    const remote = { ...BASE, elements: BASE.elements?.map((element) => ({ ...element, assignment: 'Read corner leverage' })), _revision: 5 };
    const result = mergeRemoteDesign(BASE, local, remote);
    expect(result.status).toBe('merged');
    expect(result.design?.elements?.[0]).toMatchObject({ note: 'Alert the safety', assignment: 'Read corner leverage' });
  });

  it('preserves a local deletion when the server did not touch that object', () => {
    const local = { ...BASE, players: BASE.players?.filter((player) => player.id !== 'X') };
    const remote = { ...BASE, name: 'Remote rename', _revision: 5 };
    const result = mergeRemoteDesign(BASE, local, remote);
    expect(result.status).toBe('merged');
    expect(result.design?.players?.some((player) => player.id === 'X')).toBe(false);
    expect(result.design?.name).toBe('Remote rename');
  });
});
