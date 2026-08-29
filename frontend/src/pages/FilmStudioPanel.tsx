import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react';
import { CircleDot, Eraser, Film, Mic, Pause, Pencil, Play, SkipBack, SkipForward, Square, Scissors } from 'lucide-react';

import { useSession } from '../auth/SessionContext';
import { MutationNotice } from '../components/OperationalWorkbench';
import { recordId } from '../lib/format';
import { parseFilmLinkedRecordRefs } from '../lib/filmLinks';
import type { FilmAsset, FilmClip, FilmLinkedRecordRef, PlayDesign, Point } from '../types';
import '../styles/film-studio.css';

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return '0:00';
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`;
}

export const FILM_FRAME_RATE = 30;

export function filmFrameStep(currentTime: number, direction: -1 | 1): number {
  return Math.max(0, currentTime + direction / FILM_FRAME_RATE);
}

export function FilmStudioPanel({
  asset,
  clip,
  canAuthor,
  clipPending,
  onCreateClip,
  onSaveTelestration,
  onSaveTracking,
  onSaveVoiceNote,
  playOptions,
}: {
  asset?: FilmAsset;
  clip?: FilmClip;
  canAuthor: boolean;
  clipPending: boolean;
  onCreateClip: (values: { clipId: string; assetId: string; startSeconds: number; endSeconds: number; team: string; opponent: string; situation: string }) => void;
  onSaveTelestration: (points: Point[], frameSeconds: number, playIds: string[], linkedRecordRefs: FilmLinkedRecordRef[]) => void;
  onSaveTracking: (playerId: string, point: Point, frameSeconds: number, playIds: string[], linkedRecordRefs: FilmLinkedRecordRef[]) => void;
  onSaveVoiceNote: (values: { clipId: string; frameSeconds: number; mimeType: string; audioData: string; transcript: string }) => void;
  playOptions: PlayDesign[];
}) {
  const { session } = useSession();
  const videoRef = useRef<HTMLVideoElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [source, setSource] = useState('');
  const [mediaError, setMediaError] = useState('');
  const [duration, setDuration] = useState(asset?.duration_seconds || 0);
  const [currentTime, setCurrentTime] = useState(clip?.start_seconds || 0);
  const [clipStart, setClipStart] = useState(clip?.start_seconds || 0);
  const [clipEnd, setClipEnd] = useState(clip?.end_seconds || Math.min((asset?.duration_seconds || 60), (clip?.start_seconds || 0) + 10));
  const [drawing, setDrawing] = useState<Point[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [trackingPoint, setTrackingPoint] = useState<Point | null>(null);
  const [trackingPlayer, setTrackingPlayer] = useState('');
  const [linkedPlayIds, setLinkedPlayIds] = useState<string[]>([]);
  const [linkedRecordRefsText, setLinkedRecordRefsText] = useState('');
  const [tool, setTool] = useState<'telestration' | 'tracking'>('telestration');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceError, setVoiceError] = useState('');
  const recorderRef = useRef<MediaRecorder | null>(null);
  const voiceChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    let objectUrl = '';
    let cancelled = false;
    async function loadMedia() {
      if (!asset || !session) {
        setSource('');
        return;
      }
      const candidate = asset.uri?.startsWith('http')
        ? asset.uri
        : `/v1/media/assets/${encodeURIComponent(asset.id)}/content?organization_id=${encodeURIComponent(session.organizationId)}`;
      try {
        const response = await fetch(candidate, { headers: { Authorization: `Bearer ${session.token}` } });
        if (!response.ok) throw new Error(`Media request returned ${response.status}`);
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setSource(objectUrl);
          setMediaError('');
        }
      } catch (error) {
        if (!cancelled) {
          setSource('');
          setMediaError(error instanceof Error ? error.message : 'Authorized media could not be loaded.');
        }
      }
    }
    void loadMedia();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [asset, session]);

  useEffect(() => {
    setCurrentTime(clip?.start_seconds || 0);
    setClipStart(clip?.start_seconds || 0);
    setClipEnd(clip?.end_seconds || Math.min((asset?.duration_seconds || 60), (clip?.start_seconds || 0) + 10));
    setDrawing([]);
    setTrackingPoint(null);
    setLinkedPlayIds([]);
    setLinkedRecordRefsText('');
    setTool('telestration');
    setIsRecording(false);
    setVoiceTranscript('');
    setVoiceError('');
  }, [asset?.id, clip?.id, clip?.start_seconds, clip?.end_seconds]);

  function seek(seconds: number) {
    const next = Math.min(Math.max(seconds, 0), duration || asset?.duration_seconds || 0);
    if (videoRef.current) videoRef.current.currentTime = next;
    setCurrentTime(next);
  }

  function handleStageKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return;
    if (event.key.toLowerCase() === 'j' || event.key === 'ArrowLeft') {
      event.preventDefault();
      seek(filmFrameStep(currentTime, -1));
    } else if (event.key.toLowerCase() === 'l' || event.key === 'ArrowRight') {
      event.preventDefault();
      seek(filmFrameStep(currentTime, 1));
    } else if (event.key.toLowerCase() === 'k' || event.key === ' ') {
      event.preventDefault();
      if (videoRef.current?.paused) void videoRef.current.play();
      else videoRef.current?.pause();
    }
  }

  function addPoint(event: PointerEvent<HTMLDivElement>) {
    if (!stageRef.current) return;
    const rect = stageRef.current.getBoundingClientRect();
    const point = { x: Math.round(((event.clientX - rect.left) / rect.width) * 1000) / 10, y: Math.round(((event.clientY - rect.top) / rect.height) * 1000) / 10 };
    if (tool === 'tracking') {
      setTrackingPoint(point);
      return;
    }
    if (isDrawing) setDrawing((previous) => [...previous, point]);
  }

  function startVoiceNote() {
    if (!('MediaRecorder' in window)) {
      setVoiceError('This browser does not support local voice capture. Use the transcript field instead.');
      return;
    }
    setVoiceError('');
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const recorder = new MediaRecorder(stream);
      voiceChunksRef.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size) voiceChunksRef.current.push(event.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(voiceChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = String(reader.result || '');
          if (clip && dataUrl) onSaveVoiceNote({ clipId: clip.id, frameSeconds: currentTime, mimeType: blob.type || 'audio/webm', audioData: dataUrl, transcript: voiceTranscript.trim() || `Voice note captured at ${currentTime.toFixed(2)} seconds.` });
          setIsRecording(false);
        };
        reader.readAsDataURL(blob);
      };
      recorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    }).catch((error: unknown) => setVoiceError(error instanceof Error ? error.message : 'Microphone permission was not granted.'));
  }

  function stopVoiceNote() {
    recorderRef.current?.stop();
    recorderRef.current = null;
  }

  const drawingPath = drawing.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
  const canSaveClip = Boolean(asset && clipStart >= 0 && clipEnd > clipStart && clipEnd <= (duration || asset.duration_seconds || 0));

  return (
    <section className="film-studio" aria-labelledby="film-studio-heading">
      <header className="film-studio__header">
        <div><p className="eyebrow">Film Intelligence Studio</p><h3 id="film-studio-heading">Playback, clipping, and telestration</h3><p>Work frame by frame on an authorized asset, set bounded clip boundaries, and capture visual evidence against the current football moment.</p></div>
        <span className="operational-workbench__icon" aria-hidden="true"><Film size={21} /></span>
      </header>
      <div className="film-studio__body">
        <div className="film-studio__stage-wrap">
          <div className="film-studio__stage" ref={stageRef} onKeyDown={handleStageKeyDown} onPointerDown={(event) => { if (tool === 'tracking') addPoint(event); else if (isDrawing) { stageRef.current?.setPointerCapture(event.pointerId); addPoint(event); } }} onPointerMove={tool === 'telestration' ? addPoint : undefined} onPointerUp={() => setIsDrawing(false)} role="img" tabIndex={0} aria-keyshortcuts="J K L ArrowLeft ArrowRight" aria-label="Film playback stage with telestration overlay and player tracking. Press J or left arrow for previous frame, K or space to play or pause, and L or right arrow for next frame.">
            {source ? <video aria-label={`Playback for ${asset?.id || 'film asset'}`} controls={false} onLoadedMetadata={(event) => setDuration(event.currentTarget.duration || asset?.duration_seconds || 0)} onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)} ref={videoRef} src={source} /> : <div className="film-studio__unavailable"><Film aria-hidden="true" size={28} /><strong>{mediaError ? 'Authorized media unavailable' : 'Select an authorized media asset'}</strong><span>{mediaError || 'The player will load the organization-scoped content stream here.'}</span></div>}
            <svg aria-hidden="true" className="film-studio__overlay" viewBox="0 0 100 100" preserveAspectRatio="none"><path d={drawingPath} fill="none" stroke="#53d8f9" strokeLinecap="round" strokeLinejoin="round" strokeWidth="0.65" />{trackingPoint ? <circle cx={trackingPoint.x} cy={trackingPoint.y} fill="#ffbf69" r="1.5" stroke="#fff" strokeWidth="0.45" /> : null}</svg>
          </div>
          <div className="film-studio__transport">
            <button aria-label="Step backward one frame" className="icon-button" onClick={() => seek(filmFrameStep(currentTime, -1))} type="button"><SkipBack size={16} /></button>
            <button aria-label="Play film" className="icon-button" onClick={() => void videoRef.current?.play()} type="button"><Play size={16} /></button>
            <button aria-label="Pause film" className="icon-button" onClick={() => videoRef.current?.pause()} type="button"><Pause size={16} /></button>
            <button aria-label="Step forward one frame" className="icon-button" onClick={() => seek(filmFrameStep(currentTime, 1))} type="button"><SkipForward size={16} /></button>
            <span>{formatTime(currentTime)} / {formatTime(duration || asset?.duration_seconds || 0)}</span>
            <input aria-label="Film playback timeline" max={duration || asset?.duration_seconds || 0} min="0" onChange={(event) => seek(Number(event.target.value))} step="0.01" type="range" value={Math.min(currentTime, duration || asset?.duration_seconds || 0)} />
          </div>
        </div>

        <div className="film-studio__controls">
          <div className="film-studio__tool-row"><strong>Evidence tools</strong><button className={tool === 'telestration' && isDrawing ? 'button button--primary' : 'button button--secondary'} onClick={() => { setTool('telestration'); setIsDrawing((value) => !value); }} type="button"><Pencil size={14} /> {isDrawing && tool === 'telestration' ? 'Drawing' : 'Draw'}</button><button className={tool === 'tracking' ? 'button button--primary' : 'button button--secondary'} onClick={() => { setTool('tracking'); setIsDrawing(false); }} type="button"><CircleDot size={14} /> Track player</button><button className="button button--secondary" onClick={() => { setDrawing([]); setTrackingPoint(null); }} type="button"><Eraser size={14} /> Clear</button></div>
          <p className="workbench-form__hint">Draw over the frame for telestration or select a player and place a frame-accurate tracking point. Every mark remains reviewable evidence until staff approve it.</p>
          {playOptions.length ? <label><span>Link evidence to Playbook calls <small>select canonical artifacts</small></span><select aria-label="Playbook calls linked to film evidence" multiple onChange={(event) => setLinkedPlayIds(Array.from(event.target.selectedOptions).map((option) => option.value))} size={Math.min(5, Math.max(3, playOptions.length))} value={linkedPlayIds}>{playOptions.map((play) => <option key={play.id} value={play.id}>{play.name || play.concept || play.id} · {play.unit} · v{play.version || '?'}</option>)}</select></label> : null}
          <label><span>Link evidence to downstream workspaces <small>type:id, comma separated</small></span><input aria-label="Downstream workspace links for film evidence" onChange={(event) => setLinkedRecordRefsText(event.target.value)} placeholder="scouting:SCOUT-REPORT-1, game_plan:GAMEPLAN-1" value={linkedRecordRefsText} /></label>
          {canAuthor ? <>
            <div className="film-studio__section"><div className="workbench-pane__header"><div><h4><Scissors aria-hidden="true" size={15} /> Create bounded clip</h4><p>Clip the selected authorized asset without modifying the source file.</p></div></div><div className="workbench-form__grid"><label><span>Start seconds</span><input min="0" onChange={(event) => setClipStart(Number(event.target.value))} step="0.01" type="number" value={clipStart} /></label><label><span>End seconds</span><input min="0" onChange={(event) => setClipEnd(Number(event.target.value))} step="0.01" type="number" value={clipEnd} /></label></div><div className="workbench-form__actions"><button className="button button--ghost" onClick={() => setClipStart(Math.min(currentTime, clipEnd))} type="button">Set start at current frame</button><button className="button button--ghost" onClick={() => setClipEnd(Math.max(currentTime, clipStart))} type="button">Set end at current frame</button><button className="button button--primary" disabled={!canSaveClip || clipPending} onClick={() => onCreateClip({ clipId: recordId('CLIP-'), assetId: asset!.id, startSeconds: clipStart, endSeconds: clipEnd, team: clip?.context?.team || 'TEAM-UNKNOWN', opponent: clip?.context?.opponent || 'OPPONENT-UNKNOWN', situation: clip?.context?.situation || 'Film Studio review' })} type="button"><Scissors size={14} /> Save bounded clip</button></div></div>
            <div className="film-studio__section"><div className="workbench-pane__header"><div><h4><CircleDot aria-hidden="true" size={15} /> Player tracking</h4><p>Capture a player location at the current frame for evidence-linked review.</p></div></div><label><span>Player or jersey identifier</span><input onChange={(event) => setTrackingPlayer(event.target.value)} placeholder="CB-2 or #24" value={trackingPlayer} /></label><div className="workbench-form__actions"><button className="button button--secondary" disabled={!trackingPlayer.trim() || !trackingPoint} onClick={() => { onSaveTracking(trackingPlayer.trim(), trackingPoint!, currentTime, linkedPlayIds, parseFilmLinkedRecordRefs(linkedRecordRefsText)); setTrackingPoint(null); }} type="button"><CircleDot size={14} /> Save tracking point</button><span className="workbench-form__hint">{trackingPoint ? `Frame ${currentTime.toFixed(2)}s marked.` : 'Choose Track player, then click the video frame.'}</span></div></div>
            <button className="button button--secondary" disabled={drawing.length < 2} onClick={() => onSaveTelestration(drawing, currentTime, linkedPlayIds, parseFilmLinkedRecordRefs(linkedRecordRefsText))} type="button"><Pencil size={14} /> Save telestration evidence</button>
            <div className="film-studio__section"><div className="workbench-pane__header"><div><h4><Mic aria-hidden="true" size={15} /> Voice note</h4><p>Capture a short spoken coaching note anchored to this frame; the transcript is retained for search and accessibility.</p></div></div><label><span>Transcript or coaching summary</span><textarea onChange={(event) => setVoiceTranscript(event.target.value)} placeholder="What should the staff or player notice?" value={voiceTranscript} /></label><div className="workbench-form__actions"><button className={isRecording ? 'button button--primary' : 'button button--secondary'} onClick={isRecording ? stopVoiceNote : startVoiceNote} type="button">{isRecording ? <><Square size={14} /> Stop and save</> : <><Mic size={14} /> Record voice note</>}</button><span className="workbench-form__hint">{isRecording ? 'Recording locally; stop to save the bounded note.' : 'Microphone permission is requested only when you record.'}</span></div>{voiceError ? <p className="mutation-notice mutation-notice--error" role="alert">{voiceError}</p> : null}</div>
          </> : <p className="approval-boundary">Playback is available to this role. Clip creation and evidence capture require authorized Film Room authoring access.</p>}
        </div>
      </div>
      {clipPending ? <MutationNotice error={undefined} pending success={false} successMessage="Clip saved." /> : null}
    </section>
  );
}
