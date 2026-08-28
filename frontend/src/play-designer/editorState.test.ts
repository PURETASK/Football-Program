import type { PlayAsset, PlayDesign, PlayTemplate } from '../types';
import { createEditorState, createEmptyDesign, editorReducer } from './editorState';
import { applyPlayTemplate } from './templateMaterializer';

function design(): PlayDesign {
  return {
    id: 'PD-EDITOR-TEST',
    name: 'Dagger',
    unit: 'offense',
    personnel: '11',
    formation: 'shotgun_trips',
    players: [{ id: 'X', position: 'WR', start: { x: 10, y: 30 } }],
    elements: [{ id: 'ROUTE-X', kind: 'route', type: 'post', player_id: 'X', points: [{ x: 10, y: 30 }, { x: 35, y: 8 }] }],
    timeline: { duration_ms: 3000 },
    _revision: 2,
  };
}

describe('play designer editor state', () => {
  it('creates complete 11-player offense and defense starting points', () => {
    expect(createEmptyDesign('offense').players).toHaveLength(11);
    const defense = createEmptyDesign('defense');
    expect(defense.players).toHaveLength(11);
    expect(defense.front).toBe('4-2-5_over');
    expect(defense.coverage).toBe('cover_3');
  });

  it('records football edits in bounded undo and redo history', () => {
    const initial = createEditorState(design());
    const changed = editorReducer(initial, { type: 'update_meta', patch: { formation: 'shotgun_empty' } });
    expect(changed.dirty).toBe(true);
    expect(changed.present.formation).toBe('shotgun_empty');
    const undone = editorReducer(changed, { type: 'undo' });
    expect(undone.present.formation).toBe('shotgun_trips');
    expect(editorReducer(undone, { type: 'redo' }).present.formation).toBe('shotgun_empty');
  });

  it('duplicates a selected player and carries the linked assignment', () => {
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'select', selection: { kind: 'player', id: 'X' } });
    state = editorReducer(state, { type: 'duplicate_selected' });
    expect(state.present.players).toHaveLength(2);
    expect(state.present.elements).toHaveLength(2);
    expect(state.present.elements?.[1].player_id).toBe(state.present.players?.[1].id);
  });

  it('mirrors selected geometry across the field centerline', () => {
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'select', selection: { kind: 'player', id: 'X' } });
    state = editorReducer(state, { type: 'mirror_selected' });
    expect(state.present.players?.[0].start?.x).toBe(90);
    expect(state.present.elements?.[0].points?.[0].x).toBe(90);
  });

  it('deleting a player also removes assignments owned by that player', () => {
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'select', selection: { kind: 'player', id: 'X' } });
    state = editorReducer(state, { type: 'delete_selected' });
    expect(state.present.players).toHaveLength(0);
    expect(state.present.elements).toHaveLength(0);
  });

  it('moves a player and its linked assignment as one football object', () => {
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'move_players', ids: ['X'], delta: { x: 3, y: -2 } });
    expect(state.present.players?.[0].start).toEqual({ x: 13, y: 28 });
    expect(state.present.elements?.[0].points).toEqual([{ x: 13, y: 28 }, { x: 38, y: 6 }]);
  });

  it('marquee selection de-duplicates additive results and keyboard nudges paths', () => {
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'select', selection: { kind: 'element', id: 'ROUTE-X' } });
    state = editorReducer(state, {
      type: 'select_many',
      selections: [{ kind: 'player', id: 'X' }, { kind: 'element', id: 'ROUTE-X' }],
      additive: true,
    });
    expect(state.selected).toEqual([{ kind: 'element', id: 'ROUTE-X' }, { kind: 'player', id: 'X' }]);
    state = editorReducer(state, { type: 'nudge_selected', delta: { x: 1, y: 0 } });
    expect(state.present.players?.[0].start).toEqual({ x: 11, y: 30 });
    expect(state.present.elements?.[0].points).toEqual([{ x: 11, y: 30 }, { x: 36, y: 8 }]);
  });

  it('does not move locked players or locked assignments', () => {
    const locked = design();
    locked.players![0].locked = true;
    locked.elements![0].locked = true;
    let state = createEditorState(locked);
    state = editorReducer(state, { type: 'select_many', selections: [{ kind: 'player', id: 'X' }, { kind: 'element', id: 'ROUTE-X' }] });
    state = editorReducer(state, { type: 'nudge_selected', delta: { x: 5, y: 5 } });
    expect(state.present.players?.[0].start).toEqual({ x: 10, y: 30 });
    expect(state.present.elements?.[0].points).toEqual([{ x: 10, y: 30 }, { x: 35, y: 8 }]);
  });

  it('applies an alignment preset and carries linked assignments in one history step', () => {
    const asset: PlayAsset = {
      id: 'ASSET-FORMATION-TEST',
      kind: 'formation',
      category: 'formation',
      term: 'test_set',
      unit: 'offense',
      alignment: { slots: [{ key: 'X', position: 'WR', role: 'X', x: 20, y: 25 }] },
    };
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'apply_alignment', asset, patch: { formation: asset.term } });
    expect(state.present.formation).toBe('test_set');
    expect(state.present.players?.[0]).toMatchObject({ alignment_key: 'X', position: 'WR', role: 'X', start: { x: 20, y: 25 } });
    expect(state.present.elements?.[0].points).toEqual([{ x: 20, y: 25 }, { x: 45, y: 3 }]);
    expect(state.past).toHaveLength(1);
  });

  it('moves the full unlocked call when the hash or line context changes', () => {
    let state = createEditorState(design());
    state = editorReducer(state, { type: 'apply_field_context', patch: { hash: 'right', ball_x: 62 }, translate: { x: 12, y: 0 } });
    expect(state.present.field_context).toMatchObject({ hash: 'right', ball_x: 62 });
    expect(state.present.players?.[0].start).toEqual({ x: 22, y: 30 });
    expect(state.present.elements?.[0].points).toEqual([{ x: 22, y: 30 }, { x: 47, y: 8 }]);
  });

  it('materializes a slot-relative concept with graph references and pre-snap cues', () => {
    const template: PlayTemplate = {
      id: 'TPL-TEST-DAGGER', name: 'Dagger package', unit: 'offense', formation: 'shotgun_2x2', personnel: '11', concept: 'Dagger', template_kind: 'concept_layer', layer: 'route_concept', version: '1.0.0',
      alignment: { ball: { x: 50, y: 26.5 }, slots: [
        { key: 'X', position: 'WR', role: 'X', x: 10, y: 32 },
        { key: 'Y', position: 'TE', role: 'Y', x: 72, y: 33 },
      ] },
      timeline: { duration_ms: 2800, markers: [{ id: 'READ', label: 'Read safety', kind: 'read', ms: -300 }] },
      assignments: [
        { key: 'X-CLEAR', slot: 'X', kind: 'route', type: 'go', arrow_style: 'route', points: [{ dx: 0, dy: 0 }, { dx: 0, dy: -20 }], timing: { start_ms: 0, end_ms: 2200 } },
        { key: 'Y-DIG', slot: 'Y', kind: 'route', type: 'dig', arrow_style: 'route', depends_on: ['X-CLEAR'], target_element_key: 'X-CLEAR', points: [{ dx: 0, dy: 0 }, { dx: 0, dy: -12 }, { dx: -18, dy: -12 }], timing: { start_ms: 0, end_ms: 1800 } },
      ],
    };
    const created = applyPlayTemplate(createEmptyDesign(), template);
    expect(created.players).toHaveLength(2);
    expect(created.elements).toHaveLength(2);
    expect(created.elements?.[0].points).toEqual([{ x: 10, y: 32 }, { x: 10, y: 12 }]);
    expect(created.elements?.[1].depends_on).toEqual([created.elements?.[0].id]);
    expect(created.elements?.[1].target_element_id).toBe(created.elements?.[0].id);
    expect(created.elements?.[0].timing?.phases).toHaveLength(4);
    expect(created.timeline?.markers?.some((marker) => marker.ms === -300)).toBe(true);
  });

  it('adds a compatible template layer without removing existing assignments', () => {
    const template: PlayTemplate = {
      id: 'TPL-PROTECTION', name: 'Protection', unit: 'offense', layer: 'protection', template_kind: 'protection_layer',
      assignments: [{ key: 'X-BLOCK', slot: 'X', kind: 'block', type: 'stalk', arrow_style: 'block', points: [{ dx: 0, dy: 0 }, { dx: 0, dy: -4 }], timing: { start_ms: 0, end_ms: 900 } }],
    };
    const layered = applyPlayTemplate(design(), template, 'layer');
    expect(layered.elements).toHaveLength(2);
    expect(layered.elements?.[0].id).toBe('ROUTE-X');
    expect(layered.elements?.[1]).toMatchObject({ kind: 'block', player_id: 'X', template_id: 'TPL-PROTECTION' });
    expect(layered.template_applications).toHaveLength(1);
  });
});
