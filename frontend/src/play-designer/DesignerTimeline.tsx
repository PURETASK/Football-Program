import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, CircleHelp, Flag, Pause, Play, Plus, RotateCcw, SkipBack, SkipForward, Trash2, Volume2 } from 'lucide-react';

import type { PlayDesign, PlayElement, PlayNarrationCue, PlayTimeline } from '../types';
import { defaultTimelinePhases, elementTiming, phaseAtTime } from './timelineModel';

interface TimelineProps {
  design: PlayDesign;
  selectedElement?: PlayElement;
  playbackTime: number | null;
  onPlaybackTime: (value: number | null) => void;
  onAddMarker: (ms: number) => void;
  onSelectElement?: (id: string) => void;
  onUpdateTimeline?: (timeline: PlayTimeline) => void;
}

const SPEEDS = [0.5, 1, 1.5, 2];
const MARKER_KINDS = ['snap', 'cue', 'pause', 'read', 'rotation', 'exchange', 'ball', 'handoff'] as const;

function formatTime(ms: number): string {
  const sign = ms < 0 ? '-' : '';
  return `${sign}${(Math.abs(ms) / 1000).toFixed(2)}s`;
}

function supportsReducedMotion(): boolean {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function speakCue(cue: PlayNarrationCue): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(new SpeechSynthesisUtterance(cue.text));
}

export function DesignerTimeline({ design, selectedElement, playbackTime, onPlaybackTime, onAddMarker, onSelectElement, onUpdateTimeline }: TimelineProps) {
  const elements = design.elements ?? [];
  const markers = useMemo(() => [...(design.timeline?.markers ?? [])].sort((left, right) => left.ms - right.ms), [design.timeline?.markers]);
  const narration = design.timeline?.narration ?? [];
  const events = design.timeline?.events ?? [];
  const knownStarts = [
    ...elements.map((element) => elementTiming(element).start),
    ...markers.map((marker) => marker.ms),
    ...narration.map((cue) => cue.start_ms),
    ...events.map((event) => Number(event.start_ms ?? event.ms ?? 0)),
  ].filter(Number.isFinite);
  const timelineStart = Math.min(0, ...knownStarts);
  const knownEnds = [Number(design.timeline?.duration_ms ?? 3000), ...elements.map((element) => elementTiming(element).end)].filter(Number.isFinite);
  const duration = Math.max(1000, ...knownEnds);
  const span = Math.max(1, duration - timelineStart);
  const current = playbackTime ?? duration;
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [expanded, setExpanded] = useState(false);
  const [selectedBranchId, setSelectedBranchId] = useState<string | null>(null);
  const [reducedMotion] = useState(supportsReducedMotion);
  const startRef = useRef({ clock: 0, value: 0 });
  const playbackCallbackRef = useRef(onPlaybackTime);
  const consumedPauseRef = useRef(new Set<string>());
  const activeCue = narration.find((cue) => current >= cue.start_ms && current <= cue.end_ms);

  useEffect(() => {
    playbackCallbackRef.current = onPlaybackTime;
  }, [onPlaybackTime]);

  useEffect(() => {
    if (!playing) return undefined;
    let frame = 0;
    const tick = (clock: number) => {
      const nextValue = Math.min(duration, startRef.current.value + (clock - startRef.current.clock) * speed);
      const pauseMarker = markers.find((marker) => marker.kind === 'pause' && marker.ms > startRef.current.value && marker.ms <= nextValue && !consumedPauseRef.current.has(marker.id));
      const value = pauseMarker?.ms ?? nextValue;
      playbackCallbackRef.current(value);
      if (pauseMarker) {
        consumedPauseRef.current.add(pauseMarker.id);
        setPlaying(false);
      } else if (value >= duration) {
        setPlaying(false);
      } else {
        frame = requestAnimationFrame(tick);
      }
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [duration, markers, playing, speed]);

  const jump = (value: number) => {
    setPlaying(false);
    onPlaybackTime(Math.max(timelineStart, Math.min(duration, value)));
  };

  const adjacentMarker = (direction: -1 | 1) => {
    const candidates = direction < 0 ? [...markers].reverse() : markers;
    const marker = candidates.find((item) => direction < 0 ? item.ms < current - 1 : item.ms > current + 1);
    jump(marker?.ms ?? (direction < 0 ? timelineStart : duration));
  };

  const togglePlayback = () => {
    if (reducedMotion) {
      adjacentMarker(1);
      return;
    }
    if (!playing) {
      const value = current >= duration ? timelineStart : current;
      startRef.current = { clock: performance.now(), value };
      if (value <= timelineStart) consumedPauseRef.current.clear();
    }
    setPlaying((value) => !value);
  };

  const stop = () => {
    setPlaying(false);
    consumedPauseRef.current.clear();
    onPlaybackTime(null);
  };

  const updateTimeline = (patch: Partial<PlayTimeline>) => {
    onUpdateTimeline?.({ ...design.timeline, ...patch });
  };

  const updateMarker = (id: string, patch: Partial<(typeof markers)[number]>) => {
    updateTimeline({ markers: (design.timeline?.markers ?? []).map((marker) => marker.id === id ? { ...marker, ...patch } : marker) });
  };

  const updateNarration = (id: string, patch: Partial<PlayNarrationCue>) => {
    updateTimeline({ narration: narration.map((cue) => cue.id === id ? { ...cue, ...patch } : cue) });
  };

  const addNarration = () => {
    const start = Math.max(timelineStart, Math.round(current));
    updateTimeline({ narration: [...narration, { id: `NARRATION-${Date.now().toString(36).toUpperCase()}`, role: 'coach', text: 'Explain the key, timing, and finish.', start_ms: start, end_ms: Math.min(duration, start + 900), branch_id: selectedBranchId ?? undefined }] });
  };

  const addBallEvent = () => {
    if (!selectedElement) return;
    const timing = elementTiming(selectedElement);
    const pathLabel = selectedBranchId ? selectedElement.branches?.find((branch) => branch.id === selectedBranchId)?.label ?? 'alternate path' : 'primary path';
    updateTimeline({ events: [...events, { id: `BALL-${Date.now().toString(36).toUpperCase()}`, kind: 'ball', label: `Ball follows ${selectedElement.type ?? selectedElement.kind} · ${pathLabel}`, element_id: selectedElement.id, branch_id: selectedBranchId ?? undefined, start_ms: timing.start, end_ms: timing.end }] });
  };

  const addSynchronizedEvent = (kind: 'handoff' | 'read' | 'exchange' | 'rotation') => {
    if (!selectedElement) return;
    const timing = elementTiming(selectedElement);
    const pathLabel = selectedBranchId ? selectedElement.branches?.find((branch) => branch.id === selectedBranchId)?.label ?? 'alternate path' : 'primary path';
    const label = kind === 'handoff' ? `Handoff at ${selectedElement.type ?? selectedElement.kind}` : kind === 'read' ? `QB read: ${selectedElement.type ?? selectedElement.kind}` : `${kind} with ${selectedElement.type ?? selectedElement.kind}`;
    updateTimeline({ events: [...events, { id: `${kind.toUpperCase()}-${Date.now().toString(36).toUpperCase()}`, kind, label: `${label} · ${pathLabel}`, element_id: selectedElement.id, branch_id: selectedBranchId ?? undefined, start_ms: timing.start, end_ms: timing.end }] });
  };

  const positionPercent = (value: number) => `${((value - timelineStart) / span) * 100}%`;

  return (
    <section className={`designer-timeline${expanded ? ' is-expanded' : ''}`} aria-label="Play animation timeline" data-tutorial="timeline">
      <div className="timeline-controls">
        <span className="timeline-description" title="Animate assignments, motion, player movement, ball events, reads, and teaching narration on one synchronized clock.">
          <CircleHelp aria-hidden="true" size={14} /><span><strong>Teaching timeline</strong><small>{elements.length} synchronized tracks</small></span>
        </span>
        <button type="button" aria-label="Previous timeline cue" onClick={() => adjacentMarker(-1)}><SkipBack size={15} /></button>
        <button type="button" aria-label={reducedMotion ? 'Step to next cue' : playing ? 'Pause animation' : 'Play animation'} onClick={togglePlayback}>
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button type="button" aria-label="Next timeline cue" onClick={() => adjacentMarker(1)}><SkipForward size={15} /></button>
        <button type="button" aria-label="Reset animation preview" onClick={stop}><RotateCcw size={15} /></button>
        <label className="timeline-speed"><span className="sr-only">Playback speed</span><select value={speed} onChange={(event) => { setPlaying(false); setSpeed(Number(event.target.value)); }}>{SPEEDS.map((value) => <option value={value} key={value}>{value}×</option>)}</select></label>
        <span className="timeline-time">{formatTime(current)} <small>/ {formatTime(duration)}</small></span>
        <button className="timeline-expand" type="button" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? <ChevronDown size={15} /> : <ChevronUp size={15} />} {expanded ? 'Compact' : 'Tracks'}</button>
      </div>

      <div className="timeline-overview">
        <label className="timeline-scrubber">
          <span className="sr-only">Animation time</span>
          <input type="range" min={timelineStart} max={duration} step="25" value={current} onChange={(event) => jump(Number(event.target.value))} />
        </label>
        <div className="timeline-ruler" aria-hidden="true">
          {Array.from({ length: 7 }, (_, index) => <span key={index} style={{ left: `${(index / 6) * 100}%` }}>{formatTime(timelineStart + (index / 6) * span)}</span>)}
        </div>
        <span className="timeline-playhead" aria-hidden="true" style={{ left: positionPercent(current) }} />
        <div className="timeline-markers">
          {markers.map((marker) => (
            <button key={marker.id} type="button" className={`timeline-marker timeline-marker--${marker.kind ?? 'cue'}`} style={{ left: positionPercent(marker.ms) }} title={`${marker.label} at ${formatTime(marker.ms)}`} aria-label={`Jump to ${marker.label} at ${formatTime(marker.ms)}`} onClick={() => jump(marker.ms)}><Flag size={11} /></button>
          ))}
        </div>
      </div>

      {selectedElement ? <div className="timeline-selected-readout"><strong>{selectedElement.type ?? selectedElement.kind}</strong><span>{phaseAtTime(selectedElement, current)?.label ?? (current < elementTiming(selectedElement).start ? 'Waiting' : current > elementTiming(selectedElement).end ? 'Complete' : 'In progress')}</span><small>{formatTime(elementTiming(selectedElement).start)}–{formatTime(elementTiming(selectedElement).end)}</small></div> : null}
      {activeCue ? <div className="timeline-narration-now" role="status"><span><strong>{activeCue.role ?? 'Coach'} cue</strong>{activeCue.text}</span><button type="button" aria-label="Speak current teaching cue" onClick={() => speakCue(activeCue)}><Volume2 size={15} /> Speak</button></div> : null}

      {expanded ? <div className="timeline-expanded-content">
        <div className="timeline-track-list" aria-label="Assignment timing tracks">
          {!elements.length ? <p className="timeline-empty">Draw an assignment to create its synchronized timing track.</p> : elements.map((element) => {
            const timing = elementTiming(element);
            const phases = element.timing?.phases?.length ? element.timing.phases : defaultTimelinePhases(element.kind, timing.start, timing.end);
            const active = selectedElement?.id === element.id;
            return <div className={`timeline-track-row${active ? ' is-selected' : ''}`} key={element.id}>
              <button type="button" className="timeline-track-label" aria-label={`Select ${element.type ?? element.kind} track for ${(design.players ?? []).find((player) => player.id === element.player_id)?.position ?? 'team'}`} onClick={() => onSelectElement?.(element.id)}><strong>{element.type ?? element.kind}</strong><small>{(design.players ?? []).find((player) => player.id === element.player_id)?.position ?? 'Team'}</small></button>
              <button type="button" className="timeline-track-lane" aria-label={`Jump to ${element.type ?? element.kind} start`} onClick={() => { onSelectElement?.(element.id); jump(timing.start); }}>
                <span className={`timeline-track-window timeline-track-window--${element.kind}`} style={{ left: positionPercent(timing.start), width: `${((timing.end - timing.start) / span) * 100}%` }}>
                  {phases.map((phase) => <span key={phase.id} className="timeline-track-phase" style={{ width: `${((phase.end_ms - phase.start_ms) / Math.max(1, timing.end - timing.start)) * 100}%` }} title={`${phase.label ?? phase.id}: ${formatTime(phase.start_ms)}–${formatTime(phase.end_ms)}`} />)}
                </span>
                <span className="timeline-row-playhead" aria-hidden="true" style={{ left: positionPercent(current) }} />
              </button>
            </div>;
          })}
        </div>

        <div className="timeline-cue-editor">
          <section><header><div><strong>Markers and pauses</strong><small>Step through reads, rotations, exchanges, and deliberate teaching pauses.</small></div><button type="button" onClick={() => onAddMarker(current)}><Plus size={14} /> Marker</button></header>
            <div className="timeline-editor-list">{(design.timeline?.markers ?? []).map((marker) => <div className="timeline-editor-row" key={marker.id}>
              <input aria-label={`${marker.label} label`} value={marker.label} onChange={(event) => updateMarker(marker.id, { label: event.target.value })} />
              <select aria-label={`${marker.label} kind`} value={marker.kind ?? 'cue'} onChange={(event) => updateMarker(marker.id, { kind: event.target.value })}>{MARKER_KINDS.map((kind) => <option value={kind} key={kind}>{kind}</option>)}</select>
              <input aria-label={`${marker.label} time`} type="number" min={timelineStart} max={duration} value={marker.ms} onChange={(event) => updateMarker(marker.id, { ms: Number(event.target.value) })} />
              <button type="button" aria-label={`Delete ${marker.label}`} onClick={() => updateTimeline({ markers: (design.timeline?.markers ?? []).filter((item) => item.id !== marker.id) })}><Trash2 size={14} /></button>
            </div>)}</div>
          </section>
          <section><header><div><strong>Narration</strong><small>Display and optionally speak synchronized coach language.</small></div><button type="button" onClick={addNarration}><Plus size={14} /> Cue</button></header>
            <div className="timeline-editor-list">{narration.map((cue) => <div className="timeline-editor-row timeline-editor-row--narration" key={cue.id}>
              <input aria-label="Narration role" value={cue.role ?? 'coach'} onChange={(event) => updateNarration(cue.id, { role: event.target.value })} />
              <input aria-label="Narration text" value={cue.text} onChange={(event) => updateNarration(cue.id, { text: event.target.value })} />
              <input aria-label="Narration start" type="number" min={timelineStart} max={duration} value={cue.start_ms} onChange={(event) => updateNarration(cue.id, { start_ms: Number(event.target.value) })} />
              <input aria-label="Narration end" type="number" min={timelineStart + 1} max={duration} value={cue.end_ms} onChange={(event) => updateNarration(cue.id, { end_ms: Number(event.target.value) })} />
              <button type="button" aria-label="Delete narration cue" onClick={() => updateTimeline({ narration: narration.filter((item) => item.id !== cue.id) })}><Trash2 size={14} /></button>
            </div>)}</div>
          </section>
          <section><header><div><strong>Ball and synchronized events</strong><small>Bind ball travel, handoffs, QB reads, exchanges, and rotations to canonical assignment timing.</small></div><div className="timeline-event-actions"><button type="button" aria-label="Ball on selected path" disabled={!selectedElement} onClick={addBallEvent}><Plus size={14} /> Ball</button><button type="button" disabled={!selectedElement} onClick={() => addSynchronizedEvent('handoff')}><Plus size={14} /> Handoff</button><button type="button" disabled={!selectedElement} onClick={() => addSynchronizedEvent('read')}><Plus size={14} /> QB read</button><button type="button" disabled={!selectedElement} onClick={() => addSynchronizedEvent('exchange')}><Plus size={14} /> Exchange</button><button type="button" disabled={!selectedElement} onClick={() => addSynchronizedEvent('rotation')}><Plus size={14} /> Rotation</button></div></header>
            {selectedElement?.branches?.length ? <div className="timeline-path-selector" role="group" aria-label="Timeline route path"><span>Attach cues to</span><button type="button" className={!selectedBranchId ? 'is-selected' : ''} onClick={() => setSelectedBranchId(null)}>Primary path</button>{selectedElement.branches.map((branch) => <button type="button" className={selectedBranchId === branch.id ? 'is-selected' : ''} key={branch.id} onClick={() => setSelectedBranchId(branch.id)}>{branch.label}</button>)}</div> : null}
            <div className="timeline-event-chips">{events.map((event, index) => <span key={event.id ?? `${event.kind}-${index}`}><strong>{event.kind ?? 'event'}</strong>{event.label ?? event.element_id ?? 'Timeline event'}<button type="button" aria-label={`Delete ${event.label ?? 'timeline event'}`} onClick={() => updateTimeline({ events: events.filter((_, eventIndex) => eventIndex !== index) })}><Trash2 size={12} /></button></span>)}{!events.length ? <small>No synchronized events yet.</small> : null}</div>
          </section>
        </div>
      </div> : null}

      {!expanded ? <button className="timeline-add-marker" type="button" onClick={() => onAddMarker(current)}><Plus size={14} /> Marker</button> : null}
      {reducedMotion ? <span className="timeline-reduced-motion">Reduced motion is active; Play advances cue by cue.</span> : null}
    </section>
  );
}
