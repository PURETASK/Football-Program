import { useEffect, useId, useMemo, useState } from 'react';
import { Pause, Play, RotateCcw } from 'lucide-react';

import type { PlayElement, PlayPlayer, PlayRoleView } from '../types';
import { elementPoints, positionAlongPath, smoothPathData } from './geometry';
import { defensiveExchangeLinks } from './defensiveExchanges';

function colorFor(kind: string): string {
  if (kind === 'motion') return '#b98b16';
  if (kind === 'block') return '#516275';
  if (kind === 'run') return '#16865d';
  if (['coverage', 'rotation', 'fit'].includes(kind)) return '#c16d08';
  if (['rush', 'stunt'].includes(kind)) return '#c33945';
  if (kind === 'annotation' || kind === 'read') return '#7254bf';
  return '#147c9d';
}

function playerPoint(player: PlayPlayer): { x: number; y: number } | undefined {
  return player.start;
}

export function TeachingDiagram({ view, stepIndex, onStepChange }: { view: PlayRoleView; stepIndex: number; onStepChange: (step: number) => void }) {
  const markerId = useId().replace(/:/g, '');
  const steps = view.steps ?? [];
  const safeStep = steps.length ? Math.max(0, Math.min(stepIndex, steps.length - 1)) : 0;
  const activeStep = steps[safeStep];
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(1);
  const stepElementIds = useMemo(() => new Map(steps.map((step) => [step.element_id, step.step_index ?? 0])), [steps]);
  const activeElementId = activeStep?.element_id;
  const exchangeLinks = useMemo(() => view.mode === 'coach' || view.elements.some((element) => element.exchange_with) ? defensiveExchangeLinks({ id: view.play_id, unit: 'defense', elements: view.elements }) : [], [view.elements, view.mode, view.play_id]);
  const activeExchange = activeStep?.exchange_with ? exchangeLinks.find((link) => (link.fromId === activeElementId && link.toId === activeStep.exchange_with) || (link.toId === activeElementId && link.fromId === activeStep.exchange_with)) : undefined;
  const exchangeState = activeStep?.exchange_with ? (progress < 0.5 ? 'Before exchange' : 'After exchange') : undefined;

  useEffect(() => {
    setPlaying(false);
    setProgress(1);
  }, [activeElementId]);

  useEffect(() => {
    if (!playing || !activeElementId) return undefined;
    if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      setProgress(1);
      setPlaying(false);
      return undefined;
    }
    const started = performance.now();
    const duration = Math.max(650, Math.min(2200, Number(activeStep?.end_ms ?? 1200) - Number(activeStep?.start_ms ?? 0)));
    let frame = 0;
    const tick = (now: number) => {
      const next = Math.min(1, (now - started) / duration);
      setProgress(next);
      if (next < 1) frame = requestAnimationFrame(tick);
      else setPlaying(false);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [activeElementId, activeStep?.end_ms, activeStep?.start_ms, playing]);

  const allPlayers = [...(view.context_players ?? []), ...(view.players ?? [])];
  const playerIds = new Set((view.players ?? []).map((player) => player.id));
  const canReveal = view.mode === 'coach' || safeStep >= steps.length - 1;

  return (
    <section className="teaching-diagram" aria-label="Filtered teaching diagram">
      <header className="teaching-diagram__header">
        <div><span className="designer-kicker">Filtered field view</span><strong>{view.mode === 'coach' ? 'Staff full-call view' : `${view.role.replaceAll('_', ' ')} teaching view`}</strong><small>{activeStep ? `${activeStep.label ?? 'Assignment'} · ${activeStep.start_ms ?? 0}–${activeStep.end_ms ?? 0} ms` : 'No timed assignment selected'}</small></div>
        <div className="teaching-diagram__actions">
          <button type="button" aria-label="Replay active assignment" onClick={() => { setProgress(0); setPlaying(true); }} disabled={!activeElementId}><RotateCcw size={14} /></button>
          <button type="button" aria-label={playing ? 'Pause active assignment' : 'Play active assignment'} onClick={() => { if (progress >= 1) setProgress(0); setPlaying((current) => !current); }} disabled={!activeElementId}>{playing ? <Pause size={14} /> : <Play size={14} />}</button>
        </div>
      </header>
      {activeStep && (activeStep.exchange_with || activeStep.gap_owner || activeStep.replacement_zone) ? <div className="teaching-exchange-status" role="status"><strong>{exchangeState ?? 'Responsibility context'}</strong>{activeStep.gap_owner ? <span>Owns {activeStep.gap_owner}</span> : null}{activeStep.exchange_with ? <span>{activeStep.exchange_role?.replaceAll('_', ' ') || 'exchange'} with {activeStep.exchange_with}</span> : null}{activeStep.replacement_zone ? <span>Replaces {activeStep.replacement_zone}</span> : null}{activeStep.rotation_trigger ? <span>Trigger: {activeStep.rotation_trigger.replaceAll('_', ' ')}</span> : null}</div> : null}
      <svg className="teaching-diagram__svg" viewBox="0 0 100 53" role="img" aria-label={`${view.role} filtered football diagram with ${view.elements?.length ?? 0} assignments`}>
        <defs>
          <pattern id={`${markerId}-grass`} width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="#19664f" /><rect width="5" height="10" fill="#155b47" opacity=".45" /></pattern>
          <marker id={`${markerId}-arrow`} markerHeight="5" markerWidth="5" orient="auto" refX="4.2" refY="2.5"><path d="M0,0 L5,2.5 L0,5 Z" fill="#147c9d" /></marker>
        </defs>
        <rect className="teaching-diagram__surface" width="100" height="53" rx="1.5" fill={`url(#${markerId}-grass)`} />
        <g className="teaching-diagram__markings" aria-hidden="true"><line x1="0" x2="100" y1="26.5" y2="26.5" /><line x1="0" x2="100" y1="25.9" y2="25.9" /><line x1="0" x2="100" y1="27.1" y2="27.1" /></g>
        <g className="teaching-diagram__paths">
          {(view.elements ?? []).map((element: PlayElement) => {
            const points = elementPoints(element);
            if (element.hidden || element.kind === 'annotation' || points.length < 2) return null;
            const elementStep = stepElementIds.get(element.id);
            const revealed = view.mode === 'coach' || elementStep === undefined || elementStep <= safeStep;
            if (!revealed) return null;
            const active = element.id === activeElementId;
            return <path className={`teaching-diagram__path${active ? ' is-active' : ''}`} key={element.id} d={smoothPathData(points)} stroke={colorFor(element.kind)} pathLength={1} strokeDasharray={active && playing ? 1 : undefined} strokeDashoffset={active && playing ? 1 - progress : undefined} markerEnd={`url(#${markerId}-arrow)`} aria-label={`${element.type ?? element.kind} assignment`} />;
          })}
        </g>
        {activeExchange ? <g className="teaching-exchange-overlay" role="group" aria-label={`${exchangeState ?? 'Exchange'} between ${activeExchange.fromId} and ${activeExchange.toId}`}><path d={`M ${activeExchange.from.x} ${activeExchange.from.y} Q ${(activeExchange.from.x + activeExchange.to.x) / 2} ${Math.min(activeExchange.from.y, activeExchange.to.y) - 3} ${activeExchange.to.x} ${activeExchange.to.y}`} pathLength={1} strokeDasharray={playing ? 1 : undefined} strokeDashoffset={playing ? 1 - progress : undefined} /><text x={(activeExchange.from.x + activeExchange.to.x) / 2} y={Math.min(activeExchange.from.y, activeExchange.to.y) - 4} textAnchor="middle">{exchangeState ?? activeExchange.label}</text></g> : null}
        <g className="teaching-diagram__players">
          {allPlayers.map((player: PlayPlayer) => {
            const point = playerPoint(player);
            if (!point) return null;
            const isContext = !playerIds.has(player.id);
            return <g className={`teaching-diagram__player${isContext ? ' is-context' : ''}`} key={player.id} transform={`translate(${point.x} ${point.y})`} aria-label={`${player.position ?? player.role ?? 'Player'} ${isContext ? 'context' : 'assignment'}`}><circle r="1.9" /><text y=".62">{(player.position ?? player.role ?? '?').slice(0, 3)}</text></g>;
          })}
        </g>
      </svg>
      <div className="teaching-diagram__scrubber">
        <label htmlFor="teaching-step-slider"><span>Step reveal</span><strong>{steps.length ? `${safeStep + 1} / ${steps.length}` : 'No steps'}</strong></label>
        <input id="teaching-step-slider" aria-label="Step reveal" type="range" min="0" max={Math.max(0, steps.length - 1)} value={safeStep} disabled={!steps.length} onChange={(event) => onStepChange(Number(event.target.value))} />
        <small>{canReveal ? 'All authored steps are available.' : 'Reveal steps progressively to teach the install.'}</small>
      </div>
    </section>
  );
}
