import { useId, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent, type WheelEvent as ReactWheelEvent } from 'react';

import type { PlayAsset, PlayDesign, PlayElement, PlayPlayer, PlayPresence, PlayTimelineEvent, Point } from '../types';
import type { EditorSelection, EditorTool } from './editorState';
import {
  elementPoints,
  elementProgress,
  fieldRect,
  handleRole,
  insertPointOnNearestSegment,
  normalizePoint,
  pathIntersectsRect,
  pointDistance,
  pointInRect,
  pointerToFieldPoint,
  positionAlongPath,
  polylinePathData,
  routeCollisions,
  simplifyPath,
  smoothPathData,
  translatePoints,
} from './geometry';
import { defaultTimelinePhases, elementTiming } from './timelineModel';
import { coverageShellBoxes, coverageShellLinks } from './coverageShell';
import { defensiveGapLinks } from './defensiveFront';
import { defensiveExchangeLinks, defensiveExchangeProgress } from './defensiveExchanges';
import { defensiveAlignmentLabel } from './defensiveAlignment';
import { branchProgress } from './routeBranches';
import { timelineEventEnd, timelineEventKind, timelineEventStart } from './timelineEvents';
import { routeBranchGeometryPatch, routeGeometryPatch } from './routeAuthoring';

interface CanvasProps {
  design: PlayDesign;
  compareDesign?: PlayDesign;
  compareVisible?: boolean;
  selected: EditorSelection[];
  tool: EditorTool;
  activeAsset: PlayAsset | null;
  snap: boolean;
  playbackTime: number | null;
  onSelect: (selection: EditorSelection | null, additive?: boolean) => void;
  onSelectMany: (selections: EditorSelection[], additive?: boolean) => void;
  onMovePlayers: (ids: string[], delta: Point) => void;
  onMoveElements: (ids: string[], delta: Point) => void;
  onAddElement: (element: PlayElement) => void;
  onUpdateElement: (id: string, patch: Partial<PlayElement>) => void;
  onPan?: (delta: Point) => void;
  onZoom?: (delta: number) => void;
  onCursor?: (point: Point) => void;
  presence?: PlayPresence[];
}

interface PlayerDrag {
  pointerId: number;
  ids: string[];
  origin: Point;
  current: Point;
}

interface HandleDrag {
  pointerId: number;
  elementId: string;
  pointIndex: number;
  points: Point[];
}

interface BranchHandleDrag {
  pointerId: number;
  elementId: string;
  branchId: string;
  pointIndex: number;
  points: Point[];
}

interface ElementDrag {
  pointerId: number;
  ids: string[];
  origin: Point;
  current: Point;
}

interface MarqueeDrag {
  pointerId: number;
  origin: Point;
  current: Point;
  additive: boolean;
}

interface PanDrag {
  pointerId: number;
  clientX: number;
  clientY: number;
}

const YARD_LINES = Array.from({ length: 21 }, (_, index) => index * 5);
const NUMBER_MARKS = [10, 20, 30, 40, 50, 40, 30, 20, 10];
const HASH_X = Array.from({ length: 50 }, (_, index) => index * 2 + 1);
const ARROW_MARKER_KINDS = ['route', 'motion', 'run', 'block', 'coverage', 'rush', 'stunt', 'annotation'] as const;

function selected(state: EditorSelection[], kind: EditorSelection['kind'], id: string): boolean {
  return state.some((item) => item.kind === kind && item.id === id);
}

function nearestPlayer(players: PlayPlayer[], point: Point): PlayPlayer | undefined {
  let result: PlayPlayer | undefined;
  let distance = 7;
  for (const player of players) {
    if (!player.start || player.hidden) continue;
    const candidate = pointDistance(player.start, point);
    if (candidate < distance) {
      distance = candidate;
      result = player;
    }
  }
  return result;
}

function elementColor(kind: string, unit: string): string {
  if (kind === 'motion') return '#f6cc65';
  if (kind === 'block') return '#f5f8ff';
  if (kind === 'run') return '#87f2bb';
  if (['coverage', 'rotation', 'fit'].includes(kind)) return '#ffb547';
  if (['rush', 'stunt'].includes(kind)) return '#ff6f79';
  if (kind === 'annotation' || kind === 'read') return '#c1acff';
  return unit === 'defense' ? '#ffb547' : '#55ddff';
}

function markerKind(element: PlayElement): string | null {
  const arrow = element.arrow_style ?? element.kind;
  if (arrow === 'none') return null;
  return ARROW_MARKER_KINDS.includes(arrow as typeof ARROW_MARKER_KINDS[number]) ? arrow : 'route';
}

function linePattern(style?: string): string | undefined {
  if (style === 'dashed') return '2.8 1.4';
  if (style === 'dotted') return '0.45 1';
  return undefined;
}

function defaultEndMs(kind: string): number {
  if (kind === 'motion') return 900;
  if (kind === 'block' || kind === 'rush' || kind === 'stunt') return 1800;
  return 2600;
}

function displayPlayerPoint(player: PlayPlayer, drag: PlayerDrag | null, snap: boolean): Point | undefined {
  if (!player.start || !drag?.ids.includes(player.id)) return player.start;
  return normalizePoint(
    {
      x: player.start.x + drag.current.x - drag.origin.x,
      y: player.start.y + drag.current.y - drag.origin.y,
    },
    snap,
  );
}

function displayElementPoints(element: PlayElement, playerDrag: PlayerDrag | null, elementDrag: ElementDrag | null, handleDrag: HandleDrag | null, snap: boolean): Point[] {
  let points = handleDrag?.elementId === element.id ? handleDrag.points : elementPoints(element);
  const linkedPlayerMoves = Boolean(element.player_id && playerDrag?.ids.includes(element.player_id));
  const selectedElementMoves = Boolean(elementDrag?.ids.includes(element.id));
  if (linkedPlayerMoves && playerDrag) {
    points = translatePoints(points, { x: playerDrag.current.x - playerDrag.origin.x, y: playerDrag.current.y - playerDrag.origin.y }, snap);
  } else if (selectedElementMoves && elementDrag) {
    points = translatePoints(points, { x: elementDrag.current.x - elementDrag.origin.x, y: elementDrag.current.y - elementDrag.origin.y }, snap);
  }
  return points;
}

export function PlayDesignerCanvas({
  design,
  compareDesign,
  compareVisible = false,
  selected: selection,
  tool,
  activeAsset,
  snap,
  playbackTime,
  onSelect,
  onSelectMany,
  onMovePlayers,
  onMoveElements,
  onAddElement,
  onUpdateElement,
  onPan,
  onZoom,
  onCursor,
  presence = [],
}: CanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [drawing, setDrawing] = useState<{ pointerId: number; points: Point[] } | null>(null);
  const [playerDrag, setPlayerDrag] = useState<PlayerDrag | null>(null);
  const [elementDrag, setElementDrag] = useState<ElementDrag | null>(null);
  const [handleDrag, setHandleDrag] = useState<HandleDrag | null>(null);
  const [branchHandleDrag, setBranchHandleDrag] = useState<BranchHandleDrag | null>(null);
  const [marquee, setMarquee] = useState<MarqueeDrag | null>(null);
  const [panDrag, setPanDrag] = useState<PanDrag | null>(null);
  const markerPrefix = useId().replace(/:/g, '');
  const duration = Number(design.timeline?.duration_ms ?? 3000);
  const lineOfScrimmageY = Number(design.field_context?.line_of_scrimmage_y ?? 26.5);
  const ballPoint = normalizePoint({ x: Number(design.field_context?.ball_x ?? 50), y: Number(design.field_context?.ball_y ?? lineOfScrimmageY) }, false);
  const elements = design.elements ?? [];
  const routeCollisionRecords = useMemo(() => routeCollisions(elements), [elements]);
  const routeCollisionIds = useMemo(() => new Set(routeCollisionRecords.flatMap((collision) => [collision.firstId, collision.secondId])), [routeCollisionRecords]);
  const routeCollisionByElement = useMemo(() => {
    const output = new Map<string, typeof routeCollisionRecords[number]>();
    for (const collision of routeCollisionRecords) {
      if (!output.has(collision.firstId)) output.set(collision.firstId, collision);
      if (!output.has(collision.secondId)) output.set(collision.secondId, collision);
    }
    return output;
  }, [routeCollisionRecords]);
  const players = design.players ?? [];
  const shellBoxes = useMemo(() => design.unit === 'defense' ? coverageShellBoxes(design.coverage_zones) : [], [design.coverage_zones, design.unit]);
  const shellLinks = useMemo(() => design.unit === 'defense' ? coverageShellLinks(design) : [], [design]);
  const gapLinks = useMemo(() => design.unit === 'defense' ? defensiveGapLinks(design) : [], [design]);
  const exchangeLinks = useMemo(() => design.unit === 'defense' ? defensiveExchangeLinks(design) : [], [design]);
  const selectedElement = selection.length === 1 && selection[0].kind === 'element'
    ? elements.find((element) => element.id === selection[0].id)
    : undefined;
  const selectedPoints = selectedElement
    ? displayElementPoints(selectedElement, playerDrag, elementDrag, handleDrag, snap)
    : [];

  const animatedBallPoint = useMemo(() => {
    if (playbackTime === null) return ballPoint;
    const event = (design.timeline?.events ?? []).find((item) => {
      if (!['ball', 'handoff'].includes(timelineEventKind(item))) return false;
      const start = timelineEventStart(item);
      const end = timelineEventEnd(item, duration);
      return playbackTime >= start && playbackTime <= end;
    });
    if (!event?.element_id) return ballPoint;
    const element = elements.find((item) => item.id === event.element_id);
    const points = element ? elementPoints(element) : [];
    if (!element || points.length < 2) return ballPoint;
    const timing = elementTiming(element, duration);
    const start = timelineEventStart(event) || timing.start;
    const end = timelineEventEnd(event, timing.end);
    const progress = Math.max(0, Math.min(1, (playbackTime - start) / (end - start)));
    return positionAlongPath(points, progress) ?? ballPoint;
  }, [ballPoint, design.timeline?.events, duration, elements, playbackTime]);

  const animatedPlayerPoints = useMemo(() => {
    const output = new Map<string, Point>();
    if (playbackTime === null) return output;
    const pathByPlayer = new Map<string, PlayElement>();
    for (const element of elements) {
      if (element.player_id && !pathByPlayer.has(element.player_id) && elementPoints(element).length > 1) pathByPlayer.set(element.player_id, element);
    }
    for (const player of players) {
      const element = pathByPlayer.get(player.id);
      if (!element) continue;
      const progress = elementProgress(element, playbackTime, duration);
      const point = positionAlongPath(elementPoints(element), progress);
      if (point) output.set(player.id, point);
    }
    return output;
  }, [duration, elements, playbackTime, players]);

  const activeTimelineEvents = useMemo(() => {
    if (playbackTime === null) return [];
    return (design.timeline?.events ?? []).filter((event) => {
      const start = timelineEventStart(event);
      const end = timelineEventEnd(event, duration);
      return playbackTime >= start && playbackTime <= end && !['ball', 'handoff'].includes(timelineEventKind(event));
    }).map((event: PlayTimelineEvent) => {
      const element = event.element_id ? elements.find((item) => item.id === event.element_id) : undefined;
      const point = element?.points?.at(-1) ?? element?.path?.at(-1) ?? (element?.player_id ? players.find((player) => player.id === element.player_id)?.start : undefined);
      return point ? { event, point } : null;
    }).filter((item): item is { event: PlayTimelineEvent; point: Point } => Boolean(item));
  }, [design.timeline?.events, duration, elements, playbackTime, players]);

  const eventPoint = (event: { clientX: number; clientY: number }) => {
    const bounds = svgRef.current?.getBoundingClientRect();
    return bounds ? pointerToFieldPoint(event.clientX, event.clientY, bounds, snap) : { x: 0, y: 0 };
  };

  const beginCanvasInteraction = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (event.button !== 0) return;
    event.preventDefault();
    const point = eventPoint(event);
    onCursor?.(point);
    if (tool === 'pan') {
      event.currentTarget.setPointerCapture(event.pointerId);
      setPanDrag({ pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY });
      return;
    }
    if (tool === 'select') {
      event.currentTarget.setPointerCapture(event.pointerId);
      setMarquee({
        pointerId: event.pointerId,
        origin: point,
        current: point,
        additive: event.shiftKey || event.metaKey || event.ctrlKey,
      });
      return;
    }
    if (tool === 'annotation') {
      const id = `ANNOTATION-${Date.now().toString(36).toUpperCase()}`;
      onAddElement({
        id,
        kind: 'annotation',
        type: activeAsset?.term ?? 'note',
        asset_id: activeAsset?.id,
        player_id: null,
        points: [point],
        note: 'New coaching note',
        objective: activeAsset?.description ?? 'Communicate this coaching point.',
        technique: 'teach',
        depends_on: [],
        exclusive_assignment: false,
        arrow_style: 'check',
        start_ms: 0,
        end_ms: duration,
        timing: { start_ms: 0, end_ms: duration, phases: defaultTimelinePhases('annotation', 0, duration) },
        visibility: 'shared',
      });
      return;
    }
    event.currentTarget.setPointerCapture(event.pointerId);
    setDrawing({ pointerId: event.pointerId, points: [point] });
  };

  const moveCanvasInteraction = (event: ReactPointerEvent<SVGSVGElement>) => {
    const point = eventPoint(event);
    onCursor?.(point);
    if (drawing?.pointerId === event.pointerId) {
      const last = drawing.points.at(-1)!;
      if (pointDistance(last, point) >= (snap ? 1 : 0.45)) setDrawing({ ...drawing, points: [...drawing.points, point] });
      return;
    }
    if (playerDrag?.pointerId === event.pointerId) {
      setPlayerDrag({ ...playerDrag, current: point });
      return;
    }
    if (elementDrag?.pointerId === event.pointerId) {
      setElementDrag({ ...elementDrag, current: point });
      return;
    }
    if (handleDrag?.pointerId === event.pointerId) {
      const points = handleDrag.points.map((candidate, index) => (index === handleDrag.pointIndex ? point : candidate));
      setHandleDrag({ ...handleDrag, points });
      return;
    }
    if (branchHandleDrag?.pointerId === event.pointerId) {
      const points = branchHandleDrag.points.map((candidate, index) => (index === branchHandleDrag.pointIndex ? point : candidate));
      setBranchHandleDrag({ ...branchHandleDrag, points });
      return;
    }
    if (marquee?.pointerId === event.pointerId) {
      setMarquee({ ...marquee, current: point });
      return;
    }
    if (panDrag?.pointerId === event.pointerId) {
      onPan?.({ x: panDrag.clientX - event.clientX, y: panDrag.clientY - event.clientY });
      setPanDrag({ pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY });
    }
  };

  const endCanvasInteraction = (event: ReactPointerEvent<SVGSVGElement>) => {
    const cancelled = event.type === 'pointercancel';
    if (drawing?.pointerId === event.pointerId && !cancelled) {
      const finalPoint = eventPoint(event);
      const raw = pointDistance(drawing.points.at(-1)!, finalPoint) > 0.25 ? [...drawing.points, finalPoint] : drawing.points;
      const points = simplifyPath(raw);
      if (points.length > 1 && pointDistance(points[0], points.at(-1)!) >= 2) {
        const player = nearestPlayer(players, points[0]);
        const id = `${tool.toUpperCase()}-${Date.now().toString(36).toUpperCase()}`;
        const startMs = tool === 'motion' ? -900 : 0;
        const endMs = defaultEndMs(tool);
        onAddElement({
          id,
          kind: tool,
          type: activeAsset?.term ?? tool,
          asset_id: activeAsset?.id,
          player_id: player?.id ?? null,
          points,
          arrow_style: activeAsset?.arrow_style ?? tool,
          assignment: activeAsset?.description ?? `Execute the ${activeAsset?.display_name ?? tool} assignment.`,
          objective: activeAsset?.description ?? `Execute the ${activeAsset?.display_name ?? tool} assignment.`,
          technique: activeAsset?.term ?? tool,
          depends_on: [],
          exclusive_assignment: false,
          start_ms: startMs,
          end_ms: endMs,
          timing: { start_ms: startMs, end_ms: endMs, phases: defaultTimelinePhases(tool, startMs, endMs) },
          visibility: 'shared',
        });
      }
      setDrawing(null);
    }
    if (drawing?.pointerId === event.pointerId && cancelled) setDrawing(null);
    if (playerDrag?.pointerId === event.pointerId && !cancelled) {
      const delta = {
        x: playerDrag.current.x - playerDrag.origin.x,
        y: playerDrag.current.y - playerDrag.origin.y,
      };
      if (Math.abs(delta.x) > 0.05 || Math.abs(delta.y) > 0.05) onMovePlayers(playerDrag.ids, delta);
      setPlayerDrag(null);
    }
    if (playerDrag?.pointerId === event.pointerId && cancelled) setPlayerDrag(null);
    if (elementDrag?.pointerId === event.pointerId && !cancelled) {
      const delta = {
        x: elementDrag.current.x - elementDrag.origin.x,
        y: elementDrag.current.y - elementDrag.origin.y,
      };
      if (Math.abs(delta.x) > 0.05 || Math.abs(delta.y) > 0.05) onMoveElements(elementDrag.ids, delta);
      setElementDrag(null);
    }
    if (elementDrag?.pointerId === event.pointerId && cancelled) setElementDrag(null);
    if (handleDrag?.pointerId === event.pointerId && !cancelled) {
      const element = elements.find((item) => item.id === handleDrag.elementId);
      if (element) onUpdateElement(element.id, routeGeometryPatch(element, design, handleDrag.points, handleDrag.pointIndex));
      setHandleDrag(null);
    }
    if (handleDrag?.pointerId === event.pointerId && cancelled) setHandleDrag(null);
    if (branchHandleDrag?.pointerId === event.pointerId && !cancelled) {
      const element = elements.find((item) => item.id === branchHandleDrag.elementId);
      if (element) onUpdateElement(element.id, routeBranchGeometryPatch(element, design, branchHandleDrag.branchId, branchHandleDrag.points, branchHandleDrag.pointIndex));
      setBranchHandleDrag(null);
    }
    if (branchHandleDrag?.pointerId === event.pointerId && cancelled) setBranchHandleDrag(null);
    if (marquee?.pointerId === event.pointerId) {
      if (!cancelled && pointDistance(marquee.origin, marquee.current) >= 0.75) {
        const bounds = fieldRect(marquee.origin, marquee.current);
        const selections: EditorSelection[] = [
          ...players.filter((player) => player.start && !player.hidden && pointInRect(player.start, bounds)).map((player) => ({ kind: 'player' as const, id: player.id })),
          ...elements.filter((element) => !element.hidden && pathIntersectsRect(elementPoints(element), bounds)).map((element) => ({ kind: 'element' as const, id: element.id })),
        ];
        onSelectMany(selections, marquee.additive);
      } else if (!cancelled) {
        onSelect(null);
      }
      setMarquee(null);
    }
    if (panDrag?.pointerId === event.pointerId) setPanDrag(null);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  };

  const beginPlayerDrag = (event: ReactPointerEvent<SVGGElement>, player: PlayPlayer) => {
    if (tool !== 'select' || player.locked || !player.start) return;
    event.stopPropagation();
    const additive = event.shiftKey || event.metaKey || event.ctrlKey;
    const alreadySelected = selected(selection, 'player', player.id);
    onSelect({ kind: 'player', id: player.id }, additive);
    const ids = alreadySelected
      ? selection.filter((item) => item.kind === 'player').map((item) => item.id)
      : [player.id];
    const point = eventPoint(event);
    svgRef.current?.setPointerCapture(event.pointerId);
    setPlayerDrag({ pointerId: event.pointerId, ids, origin: point, current: point });
  };

  const beginElementDrag = (event: ReactPointerEvent<SVGGElement>, element: PlayElement) => {
    if (tool !== 'select' || element.locked) return;
    event.stopPropagation();
    const additive = event.shiftKey || event.metaKey || event.ctrlKey;
    const alreadySelected = selected(selection, 'element', element.id);
    onSelect({ kind: 'element', id: element.id }, additive);
    const ids = alreadySelected
      ? selection.filter((item) => item.kind === 'element').map((item) => item.id)
      : [element.id];
    const point = eventPoint(event);
    svgRef.current?.setPointerCapture(event.pointerId);
    setElementDrag({ pointerId: event.pointerId, ids, origin: point, current: point });
  };

  const beginHandleDrag = (event: ReactPointerEvent<SVGCircleElement>, element: PlayElement, pointIndex: number) => {
    if (element.locked) return;
    event.stopPropagation();
    svgRef.current?.setPointerCapture(event.pointerId);
    setHandleDrag({ pointerId: event.pointerId, elementId: element.id, pointIndex, points: [...elementPoints(element)] });
  };

  const beginBranchHandleDrag = (event: ReactPointerEvent<SVGCircleElement>, element: PlayElement, branchId: string, pointIndex: number, points: Point[]) => {
    if (element.locked) return;
    event.stopPropagation();
    svgRef.current?.setPointerCapture(event.pointerId);
    setBranchHandleDrag({ pointerId: event.pointerId, elementId: element.id, branchId, pointIndex, points: [...points] });
  };

  const keyboardSelect = (event: ReactKeyboardEvent<SVGElement>, value: EditorSelection) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(value, event.shiftKey);
    }
  };

  const editHandleWithKeyboard = (event: ReactKeyboardEvent<SVGCircleElement>, element: PlayElement, pointIndex: number) => {
    const points = [...elementPoints(element)];
    if (event.key === 'Delete' || event.key === 'Backspace') {
      if (points.length <= 2) return;
      event.preventDefault();
      onUpdateElement(element.id, { points: points.filter((_, index) => index !== pointIndex) });
      return;
    }
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const amount = event.shiftKey ? 5 : event.altKey ? 0.1 : snap ? 1 : 0.1;
    const point = points[pointIndex];
    points[pointIndex] = normalizePoint({
      x: point.x + (event.key === 'ArrowLeft' ? -amount : event.key === 'ArrowRight' ? amount : 0),
      y: point.y + (event.key === 'ArrowUp' ? -amount : event.key === 'ArrowDown' ? amount : 0),
    }, false);
    onUpdateElement(element.id, routeGeometryPatch(element, design, points, pointIndex));
  };

  const editBranchHandleWithKeyboard = (event: ReactKeyboardEvent<SVGCircleElement>, element: PlayElement, branchId: string, pointIndex: number) => {
    const branch = element.branches?.find((item) => item.id === branchId);
    if (!branch) return;
    if (event.key === 'Delete' || event.key === 'Backspace') {
      if (branch.points.length <= 2) return;
      event.preventDefault();
      onUpdateElement(element.id, { branches: element.branches?.map((item) => item.id === branchId ? { ...item, points: item.points.filter((_, index) => index !== pointIndex) } : item) });
      return;
    }
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const amount = event.shiftKey ? 5 : event.altKey ? 0.1 : snap ? 1 : 0.1;
    const points = [...branch.points];
    const point = points[pointIndex];
    points[pointIndex] = normalizePoint({ x: point.x + (event.key === 'ArrowLeft' ? -amount : event.key === 'ArrowRight' ? amount : 0), y: point.y + (event.key === 'ArrowUp' ? -amount : event.key === 'ArrowDown' ? amount : 0) }, false);
      onUpdateElement(element.id, routeBranchGeometryPatch(element, design, branchId, points, pointIndex));
  };

  const zoomCanvas = (event: ReactWheelEvent<SVGSVGElement>) => {
    if (!onZoom || (!event.ctrlKey && !event.metaKey)) return;
    event.preventDefault();
    onZoom(event.deltaY < 0 ? 0.1 : -0.1);
  };

  const marqueeBounds = marquee ? fieldRect(marquee.origin, marquee.current) : null;

  return (
    <div className={`designer-field designer-field--${tool}${panDrag ? ' is-panning' : ''}`}>
      <svg
        ref={svgRef}
        className="designer-field__svg"
        viewBox="0 0 100 53"
        role="application"
        aria-label="Interactive football play canvas. Drag players with Select, or choose an assignment tool and drag on the field."
        onPointerDown={beginCanvasInteraction}
        onPointerMove={moveCanvasInteraction}
        onPointerUp={endCanvasInteraction}
        onPointerCancel={endCanvasInteraction}
        onWheel={zoomCanvas}
      >
        <defs>
          {['route', 'motion', 'run', 'block', 'coverage', 'rush', 'stunt', 'annotation'].map((kind) => (
            <marker key={kind} id={`${markerPrefix}-${kind}`} markerHeight="5" markerWidth="5" orient="auto-start-reverse" refX="4.2" refY="2.5">
              <path d="M0,0 L5,2.5 L0,5 Z" fill={elementColor(kind, design.unit)} />
            </marker>
          ))}
          <pattern id={`${markerPrefix}-grass`} width="10" height="10" patternUnits="userSpaceOnUse">
            <rect width="10" height="10" fill="#123d35" />
            <rect width="5" height="10" fill="#103831" opacity=".48" />
          </pattern>
          <filter id={`${markerPrefix}-shadow`} x="-60%" y="-60%" width="220%" height="220%">
            <feDropShadow dx="0" dy=".5" stdDeviation=".55" floodColor="#06130f" floodOpacity=".75" />
          </filter>
        </defs>

        <rect className="designer-field__surface" width="100" height="53" rx="1.5" fill={`url(#${markerPrefix}-grass)`} />
        <g className="designer-field__markings" aria-hidden="true">
          {YARD_LINES.map((x) => <line key={x} x1={x} x2={x} y1="0" y2="53" />)}
          <line className="designer-field__los" x1="0" x2="100" y1={lineOfScrimmageY} y2={lineOfScrimmageY} />
          {HASH_X.map((x) => (
            <g key={x}>
              <line x1={x} x2={x + 0.8} y1="18.5" y2="18.5" />
              <line x1={x} x2={x + 0.8} y1="34.5" y2="34.5" />
            </g>
          ))}
          {NUMBER_MARKS.map((number, index) => (
            <g key={`${number}-${index}`}>
              <text x={(index + 1) * 10} y="14.8">{number}</text>
              <text x={(index + 1) * 10} y="41.7" transform={`rotate(180 ${(index + 1) * 10} 39.8)`}>{number}</text>
            </g>
          ))}
        </g>

        <g className={`designer-ball-marker${playbackTime !== null && animatedBallPoint !== ballPoint ? ' is-moving' : ''}`} transform={`translate(${animatedBallPoint.x} ${animatedBallPoint.y})`} role="img" aria-label={`Ball at ${animatedBallPoint.x.toFixed(1)}, ${animatedBallPoint.y.toFixed(1)} on the synchronized timeline`}>
          <title>{`Ball · ${design.field_context?.hash ?? 'middle'} hash`}</title>
          <ellipse rx="1.15" ry="0.72" />
          <line x1="-0.55" x2="0.55" y1="0" y2="0" />
        </g>

        {marqueeBounds ? (
          <rect
            className="designer-selection-marquee"
            x={marqueeBounds.left}
            y={marqueeBounds.top}
            width={marqueeBounds.right - marqueeBounds.left}
            height={marqueeBounds.bottom - marqueeBounds.top}
            fill="rgb(85 221 255 / 0.12)"
            stroke="#55ddff"
            strokeWidth="0.3"
            strokeDasharray="1 0.6"
            vectorEffect="non-scaling-stroke"
            aria-hidden="true"
          />
        ) : null}

        {compareVisible && compareDesign ? (
          <g className="designer-compare-layer" role="group" aria-label="Version comparison overlay" pointerEvents="none">
            <g className="designer-compare-legend" transform="translate(2 2)" aria-hidden="true">
              <rect width="26" height="4.2" rx="1" />
              <line x1="1.2" x2="4.2" y1="1.5" y2="1.5" />
              <text x="5.2" y="1.85">COMPARE</text>
              <line x1="1.2" x2="4.2" y1="2.9" y2="2.9" />
              <text x="5.2" y="3.25">CURRENT</text>
            </g>
            {(compareDesign.elements ?? []).map((element) => {
              const points = elementPoints(element);
              if (element.hidden || (!points.length && element.kind !== 'annotation')) return null;
              if (element.kind === 'annotation') {
                const anchor = points[0] ?? { x: 50, y: 26 };
                return <circle className="designer-compare-annotation" key={element.id} cx={anchor.x} cy={anchor.y} r="1.7" />;
              }
              return <path className={`designer-compare-path designer-compare-path--${element.kind}`} key={element.id} d={smoothPathData(points)} />;
            })}
            {(compareDesign.players ?? []).map((player) => {
              if (player.hidden || !player.start) return null;
              const shape = compareDesign.unit === 'defense'
                ? <path className="designer-compare-player__shape" d="M-1.45,-1.45 L1.45,-1.45 L1.45,1.45 L-1.45,1.45 Z" />
                : <circle className="designer-compare-player__shape" r="1.55" />;
              return (
                <g className="designer-compare-player" key={player.id} transform={`translate(${player.start.x} ${player.start.y})`}>
                  {shape}
                  <text y=".55">{(player.position ?? player.role ?? '?').slice(0, 3)}</text>
                </g>
              );
            })}
          </g>
        ) : null}

        {shellBoxes.length ? <g className="designer-coverage-shell" role="group" aria-label="Declared coverage shell zones">
          {shellLinks.map((link) => {
            const box = shellBoxes.find((candidate) => candidate.id === link.zone);
            if (!box) return null;
            const label = `${link.owner} to ${box.label}${link.sequence !== undefined ? `, step ${link.sequence}` : ''}`;
            const midpoint = { x: (link.from.x + link.to.x) / 2, y: (link.from.y + link.to.y) / 2 };
            const reveal = playbackTime === null ? 1 : Math.max(0, Math.min(1, (playbackTime - link.startMs) / Math.max(1, link.endMs - link.startMs)));
            return <g key={link.id} className={`designer-coverage-shell__link${link.conflict ? ' is-conflict' : ''}`} role="img" aria-label={`Coverage shell movement: ${label}${link.conflict ? '; conflict: multiple owners' : ''}`}>
              <path d={smoothPathData([link.from, midpoint, link.to])} markerEnd={`url(#${markerPrefix}-coverage)`} pathLength="1" strokeDasharray={playbackTime === null ? undefined : 1} strokeDashoffset={playbackTime === null ? undefined : 1 - reveal} />
            </g>;
          })}
          {shellBoxes.map((box) => { const owners = elements.filter((element) => element.kind === 'coverage' || element.kind === 'rotation').filter((element) => element.zone === box.id || element.rotation_to_zone === box.id); const ownerLabel = owners.map((element) => `${element.player_id ?? element.type ?? element.id}${element.kind === 'rotation' && element.rotation_sequence !== undefined ? ` · step ${element.rotation_sequence}` : ''}`).join(' + ') || 'Unassigned'; return <g key={box.id} role="group" aria-label={`${box.label}: ${ownerLabel}`}>
            <rect x={box.x} y={box.y} width={box.width} height={box.height} rx="1" />
            <text x={box.x + box.width / 2} y={box.y + box.height / 2}>{box.label}</text>
            <text className="designer-coverage-shell__owner" x={box.x + box.width / 2} y={box.y + box.height / 2 + 2.5}>{ownerLabel}</text>
          </g>; })}
        </g> : null}

        {gapLinks.length ? <g className="designer-gap-ownership" role="group" aria-label="Defensive gap ownership links">
          {gapLinks.map((link) => {
            const target = { x: link.x, y: 31.2 };
            const hasOwner = Boolean(link.elementId);
            const className = `designer-gap-link${link.conflict ? ' is-conflict' : ''}${hasOwner ? ' is-owned' : ' is-unassigned'}`;
            return <g key={link.gap} className={className} role={hasOwner ? 'button' : undefined} tabIndex={hasOwner ? 0 : undefined} aria-label={`${link.label}: ${link.owner ?? 'Unassigned'}${link.conflict ? ', conflict' : ''}`} onKeyDown={(event) => { if (hasOwner && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); onSelect({ kind: 'element', id: link.elementId! }); } }} onPointerDown={(event) => { if (!hasOwner) return; event.stopPropagation(); onSelect({ kind: 'element', id: link.elementId! }); }}>
              {link.anchor ? <line x1={link.anchor.x} y1={link.anchor.y} x2={target.x} y2={target.y} /> : null}
              <circle cx={target.x} cy={target.y} r="1.35" />
              <text x={target.x} y={target.y + 3.1} textAnchor="middle">{link.gap.replace('_', ' ')}</text>
              {link.conflict ? <text x={target.x} y={target.y + 0.65} textAnchor="middle">!</text> : null}
            </g>;
          })}
        </g> : null}

        {routeCollisionRecords.length ? <g className="designer-route-collision-corridors" role="group" aria-label="Route collision corridors">
          {routeCollisionRecords.map((collision) => {
            const active = playbackTime !== null && playbackTime >= collision.overlapStartMs && playbackTime <= collision.overlapEndMs;
            const label = `${collision.firstPathLabel} and ${collision.secondPathLabel} ${collision.intentional ? 'intentional crossing' : collision.kind === 'intersection' ? 'intersection' : 'clearance corridor'}`;
            return <g className={`designer-route-collision-corridor${collision.intentional ? ' is-intentional' : ''}${active ? ' is-active' : ''}`} key={`${collision.firstId}-${collision.secondId}`} role="img" aria-label={`${label}: ${collision.explanation}`}>
              <path className="designer-route-collision-corridor__wide designer-route-collision-corridor__wide--first" d={smoothPathData(collision.firstOverlapPoints)} fill="none" strokeWidth={Math.max(1.5, collision.corridorThreshold * 2)} />
              <path className="designer-route-collision-corridor__wide designer-route-collision-corridor__wide--second" d={smoothPathData(collision.secondOverlapPoints)} fill="none" strokeWidth={Math.max(1.5, collision.corridorThreshold * 2)} />
              <path className="designer-route-collision-corridor__center" d={smoothPathData(collision.firstOverlapPoints)} fill="none" strokeWidth="0.35" />
              <title>{collision.explanation}</title>
            </g>;
          })}
        </g> : null}

        {activeTimelineEvents.length ? <g className="designer-active-timeline-events" role="group" aria-label="Active synchronized teaching events">
          {activeTimelineEvents.map(({ event, point }) => {
            const kind = timelineEventKind(event);
            const label = event.label ?? kind.replaceAll('_', ' ');
            return <g className={`designer-active-timeline-event designer-active-timeline-event--${kind}`} key={event.id ?? `${kind}-${point.x}-${point.y}`} transform={`translate(${point.x} ${point.y})`} role="img" aria-label={`Active ${kind.replaceAll('_', ' ')}: ${label}`}>
              <circle r="1.9" /><text y=".55" textAnchor="middle">{kind === 'read' ? 'R' : kind === 'rotation' ? '↻' : kind === 'exchange' || kind === 'block_exchange' || kind === 'rush_exchange' ? '↔' : kind.slice(0, 1).toUpperCase()}</text><title>{label}</title>
            </g>;
          })}
        </g> : null}

        {exchangeLinks.length ? <g className="designer-exchange-links" role="group" aria-label="Defensive exchange responsibility links">
          {exchangeLinks.map((link) => { const midX = (link.from.x + link.to.x) / 2; const midY = Math.min(link.from.y, link.to.y) - 3; const selectPair = () => onSelectMany([{ kind: 'element', id: link.fromId }, { kind: 'element', id: link.toId }]); const replacementMidX = link.replacement ? (link.to.x + link.replacement.x) / 2 : 0; const replacementMidY = link.replacement ? (link.to.y + link.replacement.y) / 2 - 2 : 0; const progress = defensiveExchangeProgress(design, link, playbackTime, duration); return <g key={link.id} role="button" tabIndex={0} aria-label={`${link.label}: ${link.fromId} with ${link.toId}${link.replacement ? `; replaces ${link.replacement.label}` : ''}`} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectPair(); } }} onPointerDown={(event) => { event.stopPropagation(); selectPair(); }}>
            <path className="designer-exchange-link__path" d={`M ${link.from.x} ${link.from.y} Q ${midX} ${midY} ${link.to.x} ${link.to.y}`} pathLength={1} strokeDasharray={playbackTime === null ? undefined : 1} strokeDashoffset={playbackTime === null ? undefined : 1 - progress} />
            <text className="designer-exchange-link__label" x={midX} y={midY - 0.8} textAnchor="middle">{link.label}</text>
            {link.replacement ? <><path className="designer-exchange-link__replacement" d={`M ${link.to.x} ${link.to.y} Q ${replacementMidX} ${replacementMidY} ${link.replacement.x} ${link.replacement.y}`} pathLength={1} strokeDasharray={playbackTime === null ? undefined : 1} strokeDashoffset={playbackTime === null ? undefined : 1 - progress} /><text className="designer-exchange-link__replacement-label" x={link.replacement.x} y={link.replacement.y - 1} textAnchor="middle">{link.replacement.label.replace('_', ' ')}</text></> : null}
          </g>; })}
        </g> : null}

        <g className="designer-field__elements">
          {elements.map((element) => {
            if (element.hidden) return null;
            const points = displayElementPoints(element, playerDrag, elementDrag, handleDrag, snap);
            const isSelected = selected(selection, 'element', element.id);
            const collision = routeCollisionByElement.get(element.id);
            const hasCollision = routeCollisionIds.has(element.id);
            const progress = playbackTime === null ? 1 : elementProgress(element, playbackTime, duration);
            if (!points.length && element.kind !== 'annotation') return null;
            if (element.kind === 'annotation') {
              const anchor = points[0] ?? { x: 50, y: 26 };
              return (
                <g
                  key={element.id}
                  className={isSelected ? 'designer-annotation is-selected' : 'designer-annotation'}
                  role="button"
                  tabIndex={0}
                  aria-label={`Annotation: ${element.note ?? element.type ?? 'coaching note'}`}
                  onKeyDown={(event) => keyboardSelect(event, { kind: 'element', id: element.id })}
                  onPointerDown={(event) => { event.stopPropagation(); onSelect({ kind: 'element', id: element.id }, event.shiftKey); }}
                >
                  <circle cx={anchor.x} cy={anchor.y} r="2.4" />
                  <text x={anchor.x} y={anchor.y + 0.65}>!</text>
                </g>
              );
            }
            const color = elementColor(element.kind, design.unit);
            const pathData = element.path_mode === 'sharp' ? polylinePathData(points) : smoothPathData(points);
            const marker = markerKind(element);
            const arrowEnds = element.arrow_ends ?? 'end';
            return (
              <g
                key={element.id}
                className="designer-element"
                role="button"
                tabIndex={0}
                  aria-label={`${element.type ?? element.kind} assignment${element.player_id ? ` for ${element.player_id}` : ''}${collision ? ` with ${collision.kind} route collision: ${collision.explanation}` : ''}`}
                onKeyDown={(event) => keyboardSelect(event, { kind: 'element', id: element.id })}
                onPointerDown={(event) => beginElementDrag(event, element)}
                onDoubleClick={(event) => {
                  if (tool !== 'select' || element.locked) return;
                  event.stopPropagation();
                  const inserted = insertPointOnNearestSegment(elementPoints(element), eventPoint(event), snap);
                  onUpdateElement(element.id, { points: inserted.points });
                }}
              >
                <path className="designer-path-hit" d={pathData} fill="none" stroke="transparent" />
                <path
                  aria-hidden="true"
                  className={`designer-path designer-path--${element.kind}${isSelected ? ' is-selected' : ''}${element.locked ? ' is-locked' : ''}`}
                  d={pathData}
                  fill="none"
                  markerEnd={marker && arrowEnds !== 'start' && arrowEnds !== 'none' ? `url(#${markerPrefix}-${marker})` : undefined}
                  markerStart={marker && (arrowEnds === 'start' || arrowEnds === 'both') ? `url(#${markerPrefix}-${marker})` : undefined}
                  pathLength={1}
                  stroke={color}
                  strokeDasharray={playbackTime === null ? linePattern(element.line_style) : 1}
                  strokeDashoffset={playbackTime === null ? undefined : 1 - progress}
                  strokeLinecap={(element.line_cap as 'round' | 'square' | 'butt' | undefined) ?? 'round'}
                  strokeLinejoin="round"
                  strokeWidth={Number(element.stroke_width ?? 0.26)}
                />
                {(element.branches ?? []).map((branch) => { const branchReveal = playbackTime === null ? 1 : branchProgress(branch, playbackTime, duration); return <path key={branch.id} className="designer-route-branch" d={smoothPathData(branch.points)} fill="none" markerEnd={marker ? `url(#${markerPrefix}-${marker})` : undefined} pathLength="1" strokeDasharray={playbackTime === null ? undefined : 1} strokeDashoffset={playbackTime === null ? undefined : 1 - branchReveal} aria-label={`${branch.label}: ${branch.condition}`} onPointerDown={(event) => { event.stopPropagation(); onSelect({ kind: 'element', id: element.id }, event.shiftKey); }} onDoubleClick={(event) => { if (tool !== 'select' || element.locked) return; event.stopPropagation(); const inserted = insertPointOnNearestSegment(branch.points, eventPoint(event), snap); onUpdateElement(element.id, { branches: element.branches?.map((candidate) => candidate.id === branch.id ? { ...candidate, points: inserted.points } : candidate) }); }} />; })}
              {collision ? <g className={`designer-collision-badge${collision.intentional ? ' is-intentional' : ''}`} aria-label={`${collision.kind === 'intersection' ? 'Route intersection' : 'Route corridor conflict'}: ${collision.explanation}`}><title>{collision.explanation}</title><circle cx={points.at(-1)?.x ?? 0} cy={points.at(-1)?.y ?? 0} r="1.25" /><text x={(points.at(-1)?.x ?? 0) - 0.42} y={(points.at(-1)?.y ?? 0) + 0.48}>{collision.intentional ? 'i' : '!'}</text></g> : null}
              </g>
            );
          })}
        </g>

        {drawing && drawing.points.length > 1 ? (
          <path
            className={`designer-path designer-path--preview designer-path--${tool}`}
            d={smoothPathData(drawing.points)}
            fill="none"
            markerEnd={`url(#${markerPrefix}-${tool})`}
            stroke={elementColor(tool, design.unit)}
          />
        ) : null}

        <g className="designer-field__players">
          {players.map((player) => {
            if (player.hidden) return null;
            const basePoint = displayPlayerPoint(player, playerDrag, snap);
            const point = animatedPlayerPoints.get(player.id) ?? basePoint;
            if (!point) return null;
            const isSelected = selected(selection, 'player', player.id);
            return (
              <g
                key={player.id}
                className={`designer-player designer-player--${design.unit}${isSelected ? ' is-selected' : ''}${player.locked ? ' is-locked' : ''}`}
                transform={`translate(${point.x} ${point.y})`}
                filter={`url(#${markerPrefix}-shadow)`}
                role="button"
                tabIndex={0}
                aria-label={`${player.position ?? player.role ?? 'Player'} at ${Math.round(point.x)}, ${Math.round(point.y)}`}
                onKeyDown={(event) => keyboardSelect(event, { kind: 'player', id: player.id })}
                onPointerDown={(event) => beginPlayerDrag(event, player)}
              >
                <circle className="designer-player__selection" r="3.25" />
                {design.unit === 'defense' ? <path className="designer-player__shape" d="M-1.7,-1.7 L1.7,-1.7 L1.7,1.7 L-1.7,1.7 Z" /> : <circle className="designer-player__shape" r="1.85" />}
                <text y=".63">{(player.position ?? player.role ?? '?').slice(0, 3)}</text>
                {design.unit === 'defense' && (player.defensive_technique || player.defensive_alignment) ? <>
                  <title>{`${player.position ?? player.role ?? 'Defender'} · ${defensiveAlignmentLabel(player)}`}</title>
                  <text className="designer-player__alignment-label" x="3.2" y="-2.6" aria-hidden="true">{defensiveAlignmentLabel(player)}</text>
                </> : null}
              </g>
            );
          })}
        </g>

        <g className="presence-cursors" aria-label="Active staff cursors">
          {presence.filter((person) => person.cursor).map((person) => {
            const point = person.cursor!;
            const label = person.display_name ?? person.subject ?? person.role ?? 'Staff';
            return (
              <g className="presence-cursor" key={person.session_id} transform={`translate(${point.x} ${point.y})`} role="img" aria-label={`${label} is editing the field`} style={{ '--presence-color': person.color ?? '#4cd6fa' } as CSSProperties}>
                <title>{`${label} is editing the field`}</title>
                <path d="M0 0 L0 4.6 L1.6 3.2 L3.3 6.6 L4.8 5.9 L3.1 2.6 L5.1 2.4 Z" />
                <rect x="5.5" y="-1.3" width={Math.max(10, Math.min(24, label.length * 1.35))} height="3.3" rx="1" />
                <text x="6.4" y="1.1">{label.slice(0, 18)}</text>
              </g>
            );
          })}
        </g>

        {selectedElement && !selectedElement.locked ? (
          <g className="designer-handles" aria-label="Editable path handles">
            {selectedPoints.map((point, index) => (
              <circle
                key={`${selectedElement.id}-${index}`}
                cx={point.x}
                cy={point.y}
                r="1.15"
                tabIndex={0}
                role="slider"
                aria-label={`Path handle ${index + 1}`}
                aria-description={`${handleRole(selectedElement, index)} handle`}
                data-handle-role={handleRole(selectedElement, index)}
                data-semantic-handle={['stem', 'break'].includes(handleRole(selectedElement, index)) ? handleRole(selectedElement, index) : undefined}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={point.x}
                aria-valuetext={`x ${point.x}, y ${point.y}`}
                onKeyDown={(event) => editHandleWithKeyboard(event, selectedElement, index)}
                onPointerDown={(event) => beginHandleDrag(event, selectedElement, index)}
                onDoubleClick={(event) => {
                  event.stopPropagation();
                  const points = elementPoints(selectedElement);
                  if (points.length > 2) onUpdateElement(selectedElement.id, { points: points.filter((_, pointIndex) => pointIndex !== index) });
                }}
              />
            ))}
            {(selectedElement.branches ?? []).map((branch) => branch.points.map((point, index) => <circle
              key={`${branch.id}-${index}`}
              className="designer-branch-handle"
              cx={point.x}
              cy={point.y}
              r=".95"
              tabIndex={0}
              role="slider"
              aria-label={`${branch.label} handle ${index + 1}`}
              aria-description={`${branch.condition}; alternate route handle`}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={point.x}
              aria-valuetext={`x ${point.x}, y ${point.y}`}
              onKeyDown={(event) => editBranchHandleWithKeyboard(event, selectedElement, branch.id, index)}
              onPointerDown={(event) => beginBranchHandleDrag(event, selectedElement, branch.id, index, branch.points)}
              onDoubleClick={(event) => {
                event.stopPropagation();
                if (branch.points.length > 2) onUpdateElement(selectedElement.id, { branches: selectedElement.branches?.map((item) => item.id === branch.id ? { ...item, points: item.points.filter((_, pointIndex) => pointIndex !== index) } : item) });
              }}
            />))}
          </g>
        ) : null}
      </svg>

      <div className="designer-field__legend" aria-hidden="true">
        <span><i className="legend-dot legend-dot--offense" /> Offense</span>
        <span><i className="legend-dot legend-dot--defense" /> Defense</span>
        <span className="designer-field__coordinates">100 × 53 canonical field · Ctrl/⌘ wheel zoom · double-click path for handle</span>
      </div>
    </div>
  );
}
