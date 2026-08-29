import type { PlayAsset, PlayDesign, PlayElement, PlayFieldContext, PlayPlayer, Point } from '../types';
import { elementPoints, mirrorPoints, normalizePoint, translatePoints } from './geometry';
import { defensiveSlotAlignmentPatch } from './defensiveAlignment';

export type EditorTool = 'select' | 'route' | 'motion' | 'run' | 'block' | 'coverage' | 'rush' | 'stunt' | 'annotation' | 'pan';
export type SelectionKind = 'player' | 'element';

export interface EditorSelection {
  kind: SelectionKind;
  id: string;
}

export interface EditorState {
  present: PlayDesign;
  past: PlayDesign[];
  future: PlayDesign[];
  selected: EditorSelection[];
  tool: EditorTool;
  activeAsset: PlayAsset | null;
  snap: boolean;
  dirty: boolean;
  savedFingerprint: string;
  serverRevision?: number;
  clipboard: { players: PlayPlayer[]; elements: PlayElement[] } | null;
}

export type EditorAction =
  | { type: 'select'; selection: EditorSelection | null; additive?: boolean }
  | { type: 'select_many'; selections: EditorSelection[]; additive?: boolean }
  | { type: 'set_tool'; tool: EditorTool; asset?: PlayAsset | null }
  | { type: 'set_asset'; asset: PlayAsset | null }
  | { type: 'toggle_snap' }
  | { type: 'update_meta'; patch: Partial<PlayDesign> }
  | { type: 'apply_alignment'; asset: PlayAsset; patch: Partial<PlayDesign> }
  | { type: 'commit_design'; design: PlayDesign }
  | { type: 'apply_field_context'; patch: Partial<PlayFieldContext>; translate?: Point }
  | { type: 'update_player'; id: string; patch: Partial<PlayPlayer> }
  | { type: 'move_players'; ids: string[]; delta: Point }
  | { type: 'move_elements'; ids: string[]; delta: Point }
  | { type: 'nudge_selected'; delta: Point }
  | { type: 'add_element'; element: PlayElement }
  | { type: 'update_element'; id: string; patch: Partial<PlayElement> }
  | { type: 'delete_selected' }
  | { type: 'duplicate_selected' }
  | { type: 'copy_selected' }
  | { type: 'paste_clipboard' }
  | { type: 'mirror_selected' }
  | { type: 'group_selected'; groupId: string }
  | { type: 'undo' }
  | { type: 'redo' }
  | { type: 'replace_design'; design: PlayDesign }
  | { type: 'recover_design'; design: PlayDesign; baseDesign: PlayDesign }
  | { type: 'mark_saved'; design: PlayDesign };

const HISTORY_LIMIT = 60;

function clone<T>(value: T): T {
  return structuredClone(value);
}

export function designFingerprint(design: PlayDesign): string {
  return JSON.stringify(design);
}

function selectionExists(design: PlayDesign, selection: EditorSelection): boolean {
  return selection.kind === 'player'
    ? (design.players ?? []).some((player) => player.id === selection.id)
    : (design.elements ?? []).some((element) => element.id === selection.id);
}

function commit(state: EditorState, next: PlayDesign, selected = state.selected): EditorState {
  const normalizedSelected = selected.filter((selection) => selectionExists(next, selection));
  return {
    ...state,
    present: next,
    past: [...state.past.slice(-(HISTORY_LIMIT - 1)), state.present],
    future: [],
    selected: normalizedSelected,
    dirty: designFingerprint(next) !== state.savedFingerprint,
  };
}

export function createEditorState(design: PlayDesign): EditorState {
  const initial = clone(design);
  return {
    present: initial,
    past: [],
    future: [],
    selected: [],
    tool: 'select',
    activeAsset: null,
    snap: true,
    dirty: false,
    savedFingerprint: designFingerprint(initial),
    serverRevision: initial._revision,
    clipboard: null,
  };
}

function updateCollection<T extends { id: string }>(items: T[] | undefined, id: string, patch: Partial<T>): T[] {
  return (items ?? []).map((item) => (item.id === id ? { ...item, ...patch } : item));
}

function uniqueCopyId(base: string, existing: Set<string>): string {
  let index = 2;
  let candidate = `${base}-COPY`;
  while (existing.has(candidate)) {
    candidate = `${base}-COPY-${index}`;
    index += 1;
  }
  return candidate;
}

const ALIGNMENT_KEYS = ['CB-L', 'CB-R', 'DE-L', 'DE-R', 'DT-L', 'DT-R', 'MLB', 'WLB', 'NB', 'FS', 'SS', 'QB', 'RB', 'LT', 'LG', 'RT', 'RG', 'X', 'Y', 'Z', 'H', 'C'];

function playerAlignmentKey(player: PlayPlayer): string | undefined {
  if (player.alignment_key) return player.alignment_key;
  const label = player.label?.toUpperCase();
  if (label && ALIGNMENT_KEYS.includes(label)) return label;
  const id = player.id.toUpperCase();
  return ALIGNMENT_KEYS.find((key) => id === key || id.endsWith(`-${key}`));
}

function translatedElement(element: PlayElement, delta: Point, snap: boolean): PlayElement {
  const points = elementPoints(element);
  if (!points.length) return element;
  const translated = translatePoints(points, delta, snap);
  return element.points ? { ...element, points: translated } : { ...element, path: translated };
}

function translateElementGeometry(element: PlayElement, delta: Point, snap: boolean): PlayElement {
  const translated = translatedElement(element, delta, snap);
  if (element.branches?.length) {
    translated.branches = element.branches.map((branch) => ({
      ...branch,
      points: translatePoints(branch.points, delta, snap),
    }));
  }
  return translated;
}

function mirrorElementGeometry(element: PlayElement): PlayElement {
  const next = { ...element };
  if (element.points) next.points = mirrorPoints(element.points);
  if (element.path) next.path = mirrorPoints(element.path);
  if (element.branches?.length) next.branches = element.branches.map((branch) => ({ ...branch, points: mirrorPoints(branch.points) }));
  if (element.finish_direction === 'inside') next.finish_direction = 'outside';
  else if (element.finish_direction === 'outside') next.finish_direction = 'inside';
  return next;
}

function remapElementReferences(element: PlayElement, ids: Map<string, string>): PlayElement {
  const next = { ...element };
  for (const key of ['target_element_id', 'block_target_element_id', 'block_partner_element_id', 'protection_target_element_id', 'exchange_with'] as const) {
    const value = next[key];
    if (typeof value === 'string' && ids.has(value)) next[key] = ids.get(value);
  }
  if (Array.isArray(next.depends_on)) next.depends_on = next.depends_on.map((id) => ids.get(id) ?? id);
  return next;
}

function moveSelection(state: EditorState, playerIds: Set<string>, elementIds: Set<string>, delta: Point): EditorState {
  const movablePlayerIds = new Set(
    (state.present.players ?? [])
      .filter((player) => playerIds.has(player.id) && !player.locked && player.start)
      .map((player) => player.id),
  );
  const movableElementIds = new Set(
    (state.present.elements ?? [])
      .filter((element) => !element.locked && (elementIds.has(element.id) || movablePlayerIds.has(element.player_id ?? '')) && elementPoints(element).length)
      .map((element) => element.id),
  );
  if (!movablePlayerIds.size && !movableElementIds.size) return state;
  const players = (state.present.players ?? []).map((player) => {
    if (!movablePlayerIds.has(player.id) || !player.start) return player;
    return { ...player, start: normalizePoint({ x: player.start.x + delta.x, y: player.start.y + delta.y }, state.snap) };
  });
  const elements = (state.present.elements ?? []).map((element) => {
    if (!movableElementIds.has(element.id)) return element;
    return translatedElement(element, delta, state.snap);
  });
  return commit(state, { ...state.present, players, elements });
}

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case 'select': {
      if (!action.selection) return { ...state, selected: [] };
      if (!action.additive) return { ...state, selected: [action.selection] };
      const alreadySelected = state.selected.some((item) => item.kind === action.selection!.kind && item.id === action.selection!.id);
      return {
        ...state,
        selected: alreadySelected
          ? state.selected.filter((item) => item.kind !== action.selection!.kind || item.id !== action.selection!.id)
          : [...state.selected, action.selection],
      };
    }
    case 'select_many': {
      const valid = action.selections.filter((selection) => selectionExists(state.present, selection));
      const combined = action.additive ? [...state.selected, ...valid] : valid;
      const seen = new Set<string>();
      const selected = combined.filter((selection) => {
        const key = `${selection.kind}:${selection.id}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      return { ...state, selected };
    }
    case 'set_tool':
      return { ...state, tool: action.tool, activeAsset: action.asset === undefined ? state.activeAsset : action.asset };
    case 'set_asset':
      return { ...state, activeAsset: action.asset };
    case 'toggle_snap':
      return { ...state, snap: !state.snap };
    case 'update_meta':
      return commit(state, { ...state.present, ...action.patch });
    case 'apply_alignment': {
      const slots = action.asset.alignment?.slots ?? [];
      if (!slots.length) return commit(state, { ...state.present, ...action.patch });
      const slotByKey = new Map(slots.map((slot) => [slot.key.toUpperCase(), slot]));
      const presetBall = action.asset.alignment?.ball;
      const ballX = Number(state.present.field_context?.ball_x ?? 50);
      const ballY = Number(state.present.field_context?.ball_y ?? state.present.field_context?.line_of_scrimmage_y ?? 26.5);
      const alignmentOffset = { x: ballX - Number(presetBall?.x ?? 50), y: ballY - Number(presetBall?.y ?? 26.5) };
      const deltas = new Map<string, Point>();
      const players = (state.present.players ?? []).map((player) => {
        if (player.locked) return player;
        const key = playerAlignmentKey(player);
        const slot = key ? slotByKey.get(key) : undefined;
        if (!slot) return player;
        const target = normalizePoint({ x: slot.x + alignmentOffset.x, y: slot.y + alignmentOffset.y }, state.snap);
        if (player.start) deltas.set(player.id, { x: target.x - player.start.x, y: target.y - player.start.y });
        return {
          ...player,
          alignment_key: key,
          position: slot.position ?? player.position,
          role: slot.role ?? player.role,
          start: target,
          ...(state.present.unit === 'defense' ? defensiveSlotAlignmentPatch(slot) : {}),
        };
      });
      const elements = (state.present.elements ?? []).map((element) => {
        const delta = element.player_id ? deltas.get(element.player_id) : undefined;
        return !delta || element.locked ? element : translatedElement(element, delta, state.snap);
      });
      return commit(state, { ...state.present, ...action.patch, players, elements });
    }
    case 'commit_design':
      return commit(state, action.design, []);
    case 'apply_field_context': {
      const translation = action.translate ?? { x: 0, y: 0 };
      const moving = Math.abs(translation.x) > 0.0001 || Math.abs(translation.y) > 0.0001;
      const movablePlayerIds = new Set((state.present.players ?? []).filter((player) => !player.locked && player.start).map((player) => player.id));
      const players = moving ? (state.present.players ?? []).map((player) => {
        if (!movablePlayerIds.has(player.id) || !player.start) return player;
        return { ...player, start: normalizePoint({ x: player.start.x + translation.x, y: player.start.y + translation.y }, state.snap) };
      }) : state.present.players;
      const elements = moving ? (state.present.elements ?? []).map((element) => {
        if (element.locked || (element.player_id && !movablePlayerIds.has(element.player_id))) return element;
        return translatedElement(element, translation, state.snap);
      }) : state.present.elements;
      return commit(state, {
        ...state.present,
        field_context: { ...state.present.field_context, ...action.patch },
        players,
        elements,
      });
    }
    case 'update_player':
      return commit(state, { ...state.present, players: updateCollection(state.present.players, action.id, action.patch) });
    case 'move_players': {
      return moveSelection(state, new Set(action.ids), new Set(), action.delta);
    }
    case 'move_elements':
      return moveSelection(state, new Set(), new Set(action.ids), action.delta);
    case 'nudge_selected':
      return moveSelection(
        state,
        new Set(state.selected.filter((item) => item.kind === 'player').map((item) => item.id)),
        new Set(state.selected.filter((item) => item.kind === 'element').map((item) => item.id)),
        action.delta,
      );
    case 'add_element':
      return commit(
        state,
        { ...state.present, elements: [...(state.present.elements ?? []), action.element] },
        [{ kind: 'element', id: action.element.id }],
      );
    case 'update_element':
      return commit(state, { ...state.present, elements: updateCollection(state.present.elements, action.id, action.patch) });
    case 'delete_selected': {
      if (!state.selected.length) return state;
      const playerIds = new Set(state.selected.filter((item) => item.kind === 'player').map((item) => item.id));
      const elementIds = new Set(state.selected.filter((item) => item.kind === 'element').map((item) => item.id));
      const players = (state.present.players ?? []).filter((player) => !playerIds.has(player.id));
      const elements = (state.present.elements ?? []).filter(
        (element) => !elementIds.has(element.id) && (!element.player_id || !playerIds.has(element.player_id)),
      );
      return commit(state, { ...state.present, players, elements }, []);
    }
    case 'duplicate_selected': {
      if (!state.selected.length) return state;
      const existingPlayerIds = new Set((state.present.players ?? []).map((item) => item.id));
      const existingElementIds = new Set((state.present.elements ?? []).map((item) => item.id));
      const playerIdMap = new Map<string, string>();
      const playerCopies = state.selected.flatMap((selection) => {
        if (selection.kind !== 'player') return [];
        const player = (state.present.players ?? []).find((item) => item.id === selection.id);
        if (!player) return [];
        const id = uniqueCopyId(player.id, existingPlayerIds);
        existingPlayerIds.add(id);
        playerIdMap.set(player.id, id);
        return [{ ...clone(player), id, start: player.start ? normalizePoint({ x: player.start.x + 3, y: player.start.y + 3 }, state.snap) : undefined }];
      });
      const selectedElementIds = new Set(state.selected.filter((item) => item.kind === 'element').map((item) => item.id));
      const copiedSourceElements = (state.present.elements ?? []).filter((element) => selectedElementIds.has(element.id) || playerIdMap.has(element.player_id ?? ''));
      const elementIdMap = new Map<string, string>();
      copiedSourceElements.forEach((element) => {
        const id = uniqueCopyId(element.id, existingElementIds);
        existingElementIds.add(id);
        elementIdMap.set(element.id, id);
      });
      const elementCopies = copiedSourceElements.map((element) => {
        const id = elementIdMap.get(element.id)!;
        const copy = remapElementReferences(translateElementGeometry(clone(element), { x: 3, y: 3 }, state.snap), elementIdMap);
        return { ...copy, id, player_id: playerIdMap.get(element.player_id ?? '') ?? element.player_id };
      });
      const next = {
        ...state.present,
        players: [...(state.present.players ?? []), ...playerCopies],
        elements: [...(state.present.elements ?? []), ...elementCopies],
      };
      const selected: EditorSelection[] = [
        ...playerCopies.map((player) => ({ kind: 'player' as const, id: player.id })),
        ...elementCopies.map((element) => ({ kind: 'element' as const, id: element.id })),
      ];
      return commit(state, next, selected);
    }
    case 'copy_selected': {
      const selectedPlayers = new Set(state.selected.filter((item) => item.kind === 'player').map((item) => item.id));
      const selectedElements = new Set(state.selected.filter((item) => item.kind === 'element').map((item) => item.id));
      const players = (state.present.players ?? []).filter((player) => selectedPlayers.has(player.id)).map(clone);
      const elements = (state.present.elements ?? []).filter((element) => selectedElements.has(element.id) || selectedPlayers.has(element.player_id ?? '')).map(clone);
      return players.length || elements.length ? { ...state, clipboard: { players, elements } } : state;
    }
    case 'paste_clipboard': {
      if (!state.clipboard || (!state.clipboard.players.length && !state.clipboard.elements.length)) return state;
      const existingPlayerIds = new Set((state.present.players ?? []).map((item) => item.id));
      const existingElementIds = new Set((state.present.elements ?? []).map((item) => item.id));
      const playerIdMap = new Map<string, string>();
      const players = state.clipboard.players.map((player) => {
        const id = uniqueCopyId(player.id, existingPlayerIds);
        existingPlayerIds.add(id);
        playerIdMap.set(player.id, id);
        return { ...clone(player), id, start: player.start ? normalizePoint({ x: player.start.x + 3, y: player.start.y + 3 }, state.snap) : undefined };
      });
      const elementIdMap = new Map<string, string>();
      state.clipboard.elements.forEach((element) => {
        const id = uniqueCopyId(element.id, existingElementIds);
        existingElementIds.add(id);
        elementIdMap.set(element.id, id);
      });
      const elements = state.clipboard.elements.map((element) => {
        const copy = remapElementReferences(translateElementGeometry(clone(element), { x: 3, y: 3 }, state.snap), elementIdMap);
        return { ...copy, id: elementIdMap.get(element.id)!, player_id: playerIdMap.get(element.player_id ?? '') ?? element.player_id };
      });
      const next = { ...state.present, players: [...(state.present.players ?? []), ...players], elements: [...(state.present.elements ?? []), ...elements] };
      return commit(state, next, [...players.map((player) => ({ kind: 'player' as const, id: player.id })), ...elements.map((element) => ({ kind: 'element' as const, id: element.id }))]);
    }
    case 'mirror_selected': {
      const selectedPlayers = new Set(state.selected.filter((item) => item.kind === 'player').map((item) => item.id));
      const selectedElements = new Set(state.selected.filter((item) => item.kind === 'element').map((item) => item.id));
      if (!selectedPlayers.size && !selectedElements.size) return state;
      const players = (state.present.players ?? []).map((player) =>
        selectedPlayers.has(player.id) && player.start
          ? { ...player, start: { x: 100 - player.start.x, y: player.start.y } }
          : player,
      );
      const elements = (state.present.elements ?? []).map((element) =>
        (selectedElements.has(element.id) || selectedPlayers.has(element.player_id ?? ''))
          ? mirrorElementGeometry(element)
          : element,
      );
      return commit(state, { ...state.present, players, elements });
    }
    case 'group_selected': {
      const selectedPlayers = new Set(state.selected.filter((item) => item.kind === 'player').map((item) => item.id));
      const selectedElements = new Set(state.selected.filter((item) => item.kind === 'element').map((item) => item.id));
      // Selecting a player means selecting that player's complete authored
      // package. This keeps grouping consistent with move, copy, and mirror.
      (state.present.elements ?? []).forEach((element) => {
        if (selectedPlayers.has(element.player_id ?? '')) selectedElements.add(element.id);
      });
      if (!selectedPlayers.size && selectedElements.size < 2) return state;
      const players = (state.present.players ?? []).map((player) => selectedPlayers.has(player.id) ? { ...player, group_id: action.groupId } : player);
      const elements = (state.present.elements ?? []).map((element) => selectedElements.has(element.id) ? { ...element, group_id: action.groupId } : element);
      return commit(state, { ...state.present, players, elements });
    }
    case 'undo': {
      const previous = state.past.at(-1);
      if (!previous) return state;
      return {
        ...state,
        present: previous,
        past: state.past.slice(0, -1),
        future: [state.present, ...state.future].slice(0, HISTORY_LIMIT),
        selected: state.selected.filter((selection) => selectionExists(previous, selection)),
        dirty: designFingerprint(previous) !== state.savedFingerprint,
      };
    }
    case 'redo': {
      const next = state.future[0];
      if (!next) return state;
      return {
        ...state,
        present: next,
        past: [...state.past, state.present].slice(-HISTORY_LIMIT),
        future: state.future.slice(1),
        selected: state.selected.filter((selection) => selectionExists(next, selection)),
        dirty: designFingerprint(next) !== state.savedFingerprint,
      };
    }
    case 'replace_design':
      return { ...createEditorState(action.design), clipboard: state.clipboard };
    case 'recover_design': {
      const recovered = createEditorState(action.design);
      return {
        ...recovered,
        dirty: designFingerprint(action.design) !== designFingerprint(action.baseDesign),
        savedFingerprint: designFingerprint(action.baseDesign),
        serverRevision: action.baseDesign._revision,
      };
    }
    case 'mark_saved': {
      const saved = clone(action.design);
      return {
        ...state,
        present: saved,
        selected: state.selected.filter((selection) => selectionExists(saved, selection)),
        savedFingerprint: designFingerprint(saved),
        serverRevision: saved._revision,
        dirty: false,
      };
    }
    default:
      return state;
  }
}

const OFFENSE_PLAYERS: Array<[string, string, number, number]> = [
  ['QB', 'QB', 50, 38], ['RB', 'RB', 57, 43], ['X', 'WR', 8, 32], ['Z', 'WR', 91, 32], ['Y', 'TE', 73, 31],
  ['H', 'WR', 82, 35], ['LT', 'LT', 38, 32], ['LG', 'LG', 44, 32], ['C', 'C', 50, 32], ['RG', 'RG', 56, 32], ['RT', 'RT', 62, 32],
];

const DEFENSE_PLAYERS: Array<[string, string, number, number]> = [
  ['DE-L', 'DE', 35, 22], ['DT-L', 'DT', 43, 22], ['DT-R', 'DT', 53, 22], ['DE-R', 'DE', 61, 22],
  ['MLB', 'MLB', 47, 16], ['WLB', 'WLB', 57, 16], ['NB', 'NB', 27, 15], ['CB-L', 'CB', 10, 21],
  ['CB-R', 'CB', 88, 21], ['SS', 'SS', 69, 10], ['FS', 'FS', 49, 6],
];

export function createEmptyDesign(unitOverride?: string): PlayDesign {
  const unit = unitOverride ?? 'offense';
  const source = unit === 'defense' ? DEFENSE_PLAYERS : OFFENSE_PLAYERS;
  const prefix = `PD-${unit === 'defense' ? 'DEF' : 'OFF'}-${Date.now().toString(36).toUpperCase()}`;
  const players = source.map(([id, position, x, y]) => ({ id: `${prefix}-${id}`, alignment_key: id, position, role: id, start: { x, y } }));
  const empty: PlayDesign = {
    id: prefix,
    name: 'Untitled play',
    concept: unit === 'defense' ? 'New defensive call' : 'New concept',
    unit,
    personnel: unit === 'defense' ? 'nickel' : '11',
    formation: unit === 'defense' ? '4-2-5_over' : 'shotgun_2x2',
    front: unit === 'defense' ? '4-2-5_over' : undefined,
    coverage: unit === 'defense' ? 'cover_3' : undefined,
    status: 'draft',
    version: '0.1.0',
    rule_profile: 'nfl',
    assignment_model_version: '1.0',
    players,
    elements: [],
    timeline: { snap_ms: 0, duration_ms: 3000, markers: [{ id: `${prefix}-SNAP`, label: 'Snap', ms: 0, kind: 'snap' }] },
    field_context: { hash: 'middle', ball_x: 50, ball_y: 26.5, line_of_scrimmage_y: 26.5, strength: 'balanced', direction: 'right', field_zone: 'open_field' },
    validation: { status: 'not_checked', issues: [] },
  };
  return empty;
}

export function assetTool(asset: PlayAsset): EditorTool {
  const kind = asset.kind as EditorTool;
  return ['route', 'motion', 'run', 'block', 'coverage', 'rush', 'stunt', 'annotation'].includes(kind) ? kind : 'select';
}
