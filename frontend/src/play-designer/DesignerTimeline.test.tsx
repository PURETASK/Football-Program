import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import type { PlayDesign } from '../types';
import { DesignerTimeline } from './DesignerTimeline';

const DESIGN: PlayDesign = {
  id: 'DESIGN-TIMELINE',
  unit: 'offense',
  players: [{ id: 'X', position: 'WR', start: { x: 10, y: 30 } }],
  elements: [{
    id: 'ROUTE-X', kind: 'route', type: 'post', player_id: 'X', points: [{ x: 10, y: 30 }, { x: 30, y: 10 }],
    start_ms: 0, end_ms: 2000,
    timing: { start_ms: 0, end_ms: 2000, phases: [{ id: 'release', label: 'Release', start_ms: 0, end_ms: 400 }, { id: 'stem', label: 'Stem', start_ms: 400, end_ms: 1100 }, { id: 'break', label: 'Break', start_ms: 1100, end_ms: 1500 }, { id: 'finish', label: 'Finish', start_ms: 1500, end_ms: 2000 }] },
  }],
  timeline: {
    duration_ms: 3000,
    markers: [{ id: 'SNAP', label: 'Snap', ms: 0, kind: 'snap' }, { id: 'READ', label: 'Read', ms: 900, kind: 'read' }, { id: 'PAUSE', label: 'Teach', ms: 1400, kind: 'pause' }],
    narration: [{ id: 'N-1', role: 'QB coach', text: 'Hold the safety with your eyes.', start_ms: 500, end_ms: 1000 }],
    events: [],
  },
  pre_snap_sequence: [{ id: 'PRE-1', kind: 'huddle', label: 'Huddle call', start_ms: -1200, end_ms: -900, notes: 'Communicate motion alert.' }],
};

describe('DesignerTimeline', () => {
  it('renders synchronized phases and lets a coach select a track', () => {
    const onSelectElement = vi.fn();
    const onPlaybackTime = vi.fn();
    render(<DesignerTimeline design={DESIGN} selectedElement={DESIGN.elements?.[0]} playbackTime={650} onPlaybackTime={onPlaybackTime} onAddMarker={vi.fn()} onSelectElement={onSelectElement} onUpdateTimeline={vi.fn()} />);
    expect(screen.getByText('Stem')).toBeInTheDocument();
    expect(screen.getByText('Hold the safety with your eyes.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Tracks/i }));
    expect(screen.getByRole('region', { name: 'Pre-snap sequence timing tracks' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Jump to Huddle call pre-snap cue' }));
    expect(onPlaybackTime).toHaveBeenCalledWith(-1200);
    fireEvent.click(screen.getByRole('button', { name: 'Select post track for WR' }));
    expect(onSelectElement).toHaveBeenCalledWith('ROUTE-X');
    expect(screen.getByTitle('Break: 1.10s–1.50s')).toBeInTheDocument();
  });

  it('steps between cues and exposes editable marker, narration, and ball-event controls', () => {
    const onPlaybackTime = vi.fn();
    const onAddMarker = vi.fn();
    const onUpdateTimeline = vi.fn();
    render(<DesignerTimeline design={DESIGN} selectedElement={DESIGN.elements?.[0]} playbackTime={100} onPlaybackTime={onPlaybackTime} onAddMarker={onAddMarker} onSelectElement={vi.fn()} onUpdateTimeline={onUpdateTimeline} />);
    fireEvent.click(screen.getByRole('button', { name: 'Next timeline cue' }));
    expect(onPlaybackTime).toHaveBeenCalledWith(900);
    fireEvent.click(screen.getByRole('button', { name: /Tracks/i }));
    fireEvent.change(screen.getByLabelText('Read label'), { target: { value: 'Quarterback read' } });
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ markers: expect.arrayContaining([expect.objectContaining({ id: 'READ', label: 'Quarterback read' })]) }));
    fireEvent.click(screen.getByRole('button', { name: 'Ball on selected path' }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: [expect.objectContaining({ kind: 'ball', element_id: 'ROUTE-X' })] }));
    fireEvent.click(screen.getByRole('button', { name: 'Cue' }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ narration: expect.arrayContaining([expect.objectContaining({ role: 'coach' })]) }));
  });

  it('binds handoff, read, exchange, and rotation cues to the selected assignment', () => {
    const onUpdateTimeline = vi.fn();
    render(<DesignerTimeline design={DESIGN} selectedElement={DESIGN.elements?.[0]} playbackTime={100} onPlaybackTime={vi.fn()} onAddMarker={vi.fn()} onSelectElement={vi.fn()} onUpdateTimeline={onUpdateTimeline} />);
    fireEvent.click(screen.getByRole('button', { name: 'Tracks' }));
    fireEvent.click(screen.getByRole('button', { name: 'Handoff' }));
    fireEvent.click(screen.getByRole('button', { name: 'QB read' }));
    fireEvent.click(screen.getByRole('button', { name: 'Exchange' }));
    fireEvent.click(screen.getByRole('button', { name: 'Block exchange' }));
    fireEvent.click(screen.getByRole('button', { name: 'Rush exchange' }));
    fireEvent.click(screen.getByRole('button', { name: 'Rotation' }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'handoff', element_id: 'ROUTE-X' })]) }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'read', element_id: 'ROUTE-X' })]) }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'exchange', element_id: 'ROUTE-X' })]) }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'block_exchange', element_id: 'ROUTE-X' })]) }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'rush_exchange', element_id: 'ROUTE-X' })]) }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'rotation', element_id: 'ROUTE-X' })]) }));
  });

  it('attaches synchronized cues to a selected alternate route branch', () => {
    const onUpdateTimeline = vi.fn();
    const design = { ...DESIGN, elements: [{ ...DESIGN.elements![0], branches: [{ id: 'BR-1', label: 'Convert out', condition: 'If corner squats', points: [{ x: 30, y: 10 }, { x: 45, y: 12 }] }] }] };
    render(<DesignerTimeline design={design} selectedElement={design.elements?.[0]} playbackTime={100} onPlaybackTime={vi.fn()} onAddMarker={vi.fn()} onSelectElement={vi.fn()} onUpdateTimeline={onUpdateTimeline} />);
    fireEvent.click(screen.getByRole('button', { name: 'Tracks' }));
    fireEvent.click(screen.getByRole('button', { name: 'Convert out' }));
    fireEvent.click(screen.getByRole('button', { name: 'QB read' }));
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: expect.arrayContaining([expect.objectContaining({ kind: 'read', branch_id: 'BR-1', label: expect.stringContaining('Convert out') })]) }));
  });

  it('allows coaches to retime a selected phase and edit synchronized event timing', () => {
    const onUpdateElement = vi.fn();
    const onUpdateTimeline = vi.fn();
    const design = { ...DESIGN, timeline: { ...DESIGN.timeline, events: [{ id: 'READ-EVENT', kind: 'read', label: 'Boundary safety', start_ms: 700, end_ms: 1100, element_id: 'ROUTE-X' }] } };
    render(<DesignerTimeline design={design} selectedElement={design.elements?.[0]} playbackTime={700} onPlaybackTime={vi.fn()} onAddMarker={vi.fn()} onSelectElement={vi.fn()} onUpdateElement={onUpdateElement} onUpdateTimeline={onUpdateTimeline} />);
    fireEvent.click(screen.getByRole('button', { name: /Tracks/i }));
    fireEvent.change(screen.getByLabelText('Stem start milliseconds'), { target: { value: '450' } });
    expect(onUpdateElement).toHaveBeenCalledWith('ROUTE-X', expect.objectContaining({ timing: expect.objectContaining({ phases: expect.arrayContaining([expect.objectContaining({ id: 'stem', start_ms: 450 })]) }) }));
    fireEvent.change(screen.getByLabelText('Synchronized event 1 start'), { target: { value: '800' } });
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: [expect.objectContaining({ id: 'READ-EVENT', start_ms: 800, ms: 800 })] }));
  });

  it('renders synchronized events as timing lanes beside assignment tracks', () => {
    const design = { ...DESIGN, timeline: { ...DESIGN.timeline, events: [{ id: 'BR-EVENT', kind: 'block_exchange', label: 'Combo exchange', element_id: 'ROUTE-X', start_ms: 300, end_ms: 700 }] } };
    render(<DesignerTimeline design={design} selectedElement={design.elements?.[0]} playbackTime={350} onPlaybackTime={vi.fn()} onAddMarker={vi.fn()} onSelectElement={vi.fn()} onUpdateTimeline={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Tracks/i }));
    expect(screen.getByRole('region', { name: 'Synchronized event timing tracks' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Jump to Combo exchange event' })).toBeInTheDocument();
  });

  it('retargets an existing synchronized event to an alternate route path', () => {
    const onUpdateTimeline = vi.fn();
    const design = {
      ...DESIGN,
      elements: [{ ...DESIGN.elements![0], branches: [{ id: 'BR-1', label: 'Convert out', condition: 'If corner squats', points: [{ x: 30, y: 10 }, { x: 45, y: 12 }] }] }],
      timeline: { ...DESIGN.timeline, events: [{ id: 'READ-EVENT', kind: 'read', label: 'Read leverage', element_id: 'ROUTE-X', start_ms: 500, end_ms: 900 }] },
    };
    render(<DesignerTimeline design={design} selectedElement={design.elements?.[0]} playbackTime={500} onPlaybackTime={vi.fn()} onAddMarker={vi.fn()} onSelectElement={vi.fn()} onUpdateTimeline={onUpdateTimeline} />);
    fireEvent.click(screen.getByRole('button', { name: /Tracks/i }));
    fireEvent.change(screen.getByLabelText('Synchronized event 1 path'), { target: { value: 'BR-1' } });
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ events: [expect.objectContaining({ id: 'READ-EVENT', branch_id: 'BR-1' })] }));
  });

  it('retargets an existing narration cue to an alternate route path', () => {
    const onUpdateTimeline = vi.fn();
    const design = {
      ...DESIGN,
      elements: [{ ...DESIGN.elements![0], branches: [{ id: 'BR-1', label: 'Convert out', condition: 'If corner squats', points: [{ x: 30, y: 10 }, { x: 45, y: 12 }] }] }],
    };
    render(<DesignerTimeline design={design} selectedElement={design.elements?.[0]} playbackTime={500} onPlaybackTime={vi.fn()} onAddMarker={vi.fn()} onSelectElement={vi.fn()} onUpdateTimeline={onUpdateTimeline} />);
    fireEvent.click(screen.getByRole('button', { name: /Tracks/i }));
    fireEvent.change(screen.getByLabelText('Narration N-1 path'), { target: { value: 'BR-1' } });
    expect(onUpdateTimeline).toHaveBeenCalledWith(expect.objectContaining({ narration: [expect.objectContaining({ id: 'N-1', branch_id: 'BR-1' })] }));
  });
});
