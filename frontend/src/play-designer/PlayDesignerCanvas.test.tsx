import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import type { PlayDesign } from '../types';
import { PlayDesignerCanvas } from './PlayDesignerCanvas';

const DESIGN: PlayDesign = {
  id: 'PD-CANVAS-TEST',
  name: 'Dagger',
  unit: 'offense',
  players: [{ id: 'X', position: 'WR', start: { x: 10, y: 30 } }],
  elements: [{ id: 'ROUTE-X', kind: 'route', type: 'post', player_id: 'X', points: [{ x: 10, y: 30 }, { x: 34, y: 8 }] }],
  timeline: { duration_ms: 3000 },
};

function props() {
  return {
    design: DESIGN,
    selected: [] as Array<{ kind: 'player' | 'element'; id: string }>,
    tool: 'select' as const,
    activeAsset: null,
    snap: true,
    playbackTime: null,
    onSelect: vi.fn(),
    onSelectMany: vi.fn(),
    onMovePlayers: vi.fn(),
    onMoveElements: vi.fn(),
    onAddElement: vi.fn(),
    onUpdateElement: vi.fn(),
  };
}

function prepareCanvas(canvas: HTMLElement) {
  Object.defineProperties(canvas, {
    getBoundingClientRect: { value: () => ({ left: 0, top: 0, width: 1000, height: 530, right: 1000, bottom: 530, x: 0, y: 0, toJSON: () => ({}) }) },
    setPointerCapture: { value: vi.fn() },
    hasPointerCapture: { value: () => false },
    releasePointerCapture: { value: vi.fn() },
  });
}

describe('PlayDesignerCanvas', () => {
  it('exposes players and assignments as keyboard-selectable canvas objects', () => {
    const callbacks = props();
    render(<PlayDesignerCanvas {...callbacks} />);
    fireEvent.keyDown(screen.getByRole('button', { name: 'WR at 10, 30' }), { key: 'Enter' });
    expect(callbacks.onSelect).toHaveBeenCalledWith({ kind: 'player', id: 'X' }, false);
    expect(screen.getByRole('button', { name: 'post assignment for X' })).toBeInTheDocument();
  });

  it('converts a real pointer drag into a registry-ready route', () => {
    const callbacks = { ...props(), tool: 'route' as const };
    render(<PlayDesignerCanvas {...callbacks} />);
    const canvas = screen.getByRole('application');
    prepareCanvas(canvas);
    fireEvent.pointerDown(canvas, { pointerId: 4, button: 0, clientX: 100, clientY: 300 });
    fireEvent.pointerMove(canvas, { pointerId: 4, clientX: 220, clientY: 190 });
    fireEvent.pointerMove(canvas, { pointerId: 4, clientX: 360, clientY: 90 });
    fireEvent.pointerUp(canvas, { pointerId: 4, clientX: 470, clientY: 90 });
    expect(callbacks.onAddElement).toHaveBeenCalledOnce();
    expect(callbacks.onAddElement.mock.calls[0][0]).toMatchObject({ kind: 'route', player_id: 'X', arrow_style: 'route' });
    expect(callbacks.onAddElement.mock.calls[0][0].points.length).toBeGreaterThan(1);
  });

  it('renders active staff cursors as accessible shared-field overlays', () => {
    const callbacks = props();
    render(<PlayDesignerCanvas {...callbacks} presence={[{ session_id: 'SESSION-2', display_name: 'Coach Smith', role: 'coach_staff', cursor: { x: 52, y: 24 }, color: '#f6cc65' }]} />);
    expect(screen.getByRole('img', { name: 'Coach Smith is editing the field' })).toBeInTheDocument();
  });

  it('renders a non-interactive visual version comparison overlay', () => {
    const callbacks = props();
    render(<PlayDesignerCanvas {...callbacks} compareVisible compareDesign={{ ...DESIGN, name: 'Dagger v1', elements: [{ ...DESIGN.elements![0], points: [{ x: 10, y: 30 }, { x: 28, y: 12 }] }] }} />);
    expect(screen.getByRole('group', { name: 'Version comparison overlay' })).toBeInTheDocument();
    expect(screen.getByText('COMPARE')).toBeInTheDocument();
  });

  it('renders the canonical ball and movable line context', () => {
    const callbacks = props();
    render(<PlayDesignerCanvas {...callbacks} design={{ ...DESIGN, field_context: { hash: 'left', ball_x: 38, ball_y: 20, line_of_scrimmage_y: 20 } }} />);
    expect(screen.getByRole('img', { name: 'Ball at 38.0, 20.0 on the synchronized timeline' })).toBeInTheDocument();
  });

  it('selects both sides when a defensive exchange link is activated', () => {
    const callbacks = props();
    const design: PlayDesign = { ...DESIGN, unit: 'defense', elements: [
      { id: 'RUSH-1', kind: 'rush', player_id: 'DE', exchange_with: 'DROP-1', exchange_role: 'penetrate_loop', points: [{ x: 35, y: 20 }, { x: 42, y: 28 }] },
      { id: 'DROP-1', kind: 'coverage', player_id: 'LB', exchange_with: 'RUSH-1', exchange_role: 'loop_penetrate', points: [{ x: 48, y: 20 }, { x: 46, y: 29 }] },
    ] };
    render(<PlayDesignerCanvas {...callbacks} design={design} />);
    const exchange = screen.getByRole('button', { name: 'Loop → penetrate: DROP-1 with RUSH-1' });
    fireEvent.keyDown(exchange, { key: 'Enter' });
    expect(callbacks.onSelectMany).toHaveBeenCalledWith([{ kind: 'element', id: 'DROP-1' }, { kind: 'element', id: 'RUSH-1' }]);
  });

  it('moves the football along a synchronized ball event', () => {
    const callbacks = props();
    render(<PlayDesignerCanvas {...callbacks} playbackTime={500} design={{ ...DESIGN, timeline: { duration_ms: 3000, events: [{ id: 'BALL-1', kind: 'ball', element_id: 'ROUTE-X', start_ms: 0, end_ms: 1000 }] } }} />);
    expect(screen.getByRole('img', { name: 'Ball at 22.0, 19.0 on the synchronized timeline' })).toBeInTheDocument();
  });

  it('marquee-selects players and paths crossing a blank-field drag', () => {
    const callbacks = props();
    render(<PlayDesignerCanvas {...callbacks} />);
    const canvas = screen.getByRole('application');
    prepareCanvas(canvas);
    fireEvent.pointerDown(canvas, { pointerId: 8, button: 0, clientX: 50, clientY: 250 });
    fireEvent.pointerMove(canvas, { pointerId: 8, clientX: 150, clientY: 350 });
    fireEvent.pointerUp(canvas, { pointerId: 8, clientX: 150, clientY: 350 });
    expect(callbacks.onSelectMany).toHaveBeenCalledWith([
      { kind: 'player', id: 'X' },
      { kind: 'element', id: 'ROUTE-X' },
    ], false);
  });

  it('turns the pan tool into viewport movement and supports wheel zoom', () => {
    const callbacks = { ...props(), tool: 'pan' as const, onPan: vi.fn(), onZoom: vi.fn() };
    render(<PlayDesignerCanvas {...callbacks} />);
    const canvas = screen.getByRole('application');
    prepareCanvas(canvas);
    fireEvent.pointerDown(canvas, { pointerId: 9, button: 0, clientX: 500, clientY: 250 });
    fireEvent.pointerMove(canvas, { pointerId: 9, clientX: 450, clientY: 220 });
    fireEvent.pointerUp(canvas, { pointerId: 9, clientX: 450, clientY: 220 });
    fireEvent.wheel(canvas, { ctrlKey: true, deltaY: -100 });
    expect(callbacks.onPan).toHaveBeenCalledWith({ x: 50, y: 30 });
    expect(callbacks.onZoom).toHaveBeenCalledWith(0.1);
  });

  it('supports keyboard path precision and double-click handle insertion', () => {
    const callbacks = { ...props(), selected: [{ kind: 'element' as const, id: 'ROUTE-X' }] };
    render(<PlayDesignerCanvas {...callbacks} />);
    const canvas = screen.getByRole('application');
    prepareCanvas(canvas);
    fireEvent.keyDown(screen.getByRole('slider', { name: 'Path handle 1' }), { key: 'ArrowRight' });
    expect(callbacks.onUpdateElement).toHaveBeenCalledWith('ROUTE-X', { points: [{ x: 11, y: 30 }, { x: 34, y: 8 }] });

    fireEvent.doubleClick(screen.getByRole('button', { name: 'post assignment for X' }), { clientX: 220, clientY: 190 });
    expect(callbacks.onUpdateElement.mock.calls.at(-1)?.[1].points).toHaveLength(3);
  });
});
