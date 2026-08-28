import { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Download, FileCheck2, LoaderCircle, X } from 'lucide-react';

import { useSession } from '../auth/SessionContext';
import { useModalFocusTrap } from '../hooks/useModalFocusTrap';
import { exportPlayDesign, preflightPlayDesignExport } from '../lib/api';
import type { ExportArtifact, ExportPreflight, PlayDesign } from '../types';

function defaultLayout(kind: string): string {
  if (kind === 'call_sheet') return 'table';
  if (kind === 'wristband') return 'wristband_2col';
  return 'single';
}

function downloadArtifact(artifact: ExportArtifact) {
  const binary = atob(artifact.content_base64);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: artifact.mime_type || 'application/octet-stream' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = artifact.filename || 'play-export';
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 750);
}

export function DesignerExportDialog({ design, designs, open, onClose }: { design: PlayDesign; designs: PlayDesign[]; open: boolean; onClose: () => void }) {
  const { session } = useSession();
  const dialogRef = useRef<HTMLElement>(null);
  const initialRef = useRef<HTMLSelectElement>(null);
  const [kind, setKind] = useState('play_card');
  const [format, setFormat] = useState('pdf');
  const [layout, setLayout] = useState('single');
  const [blackWhite, setBlackWhite] = useState(false);
  const [role, setRole] = useState('coach');
  const [selectedDesignIds, setSelectedDesignIds] = useState<string[]>([design.id]);
  const [artifact, setArtifact] = useState<ExportArtifact | null>(null);
  const [preflight, setPreflight] = useState<ExportPreflight | null>(null);
  const [preflightSignature, setPreflightSignature] = useState('');
  const [preflightBusy, setPreflightBusy] = useState(false);
  const [preflightError, setPreflightError] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useModalFocusTrap(open, dialogRef, initialRef, onClose);

  const singleDesignFormat = format === 'svg' || format === 'png';
  const availableDesigns = useMemo(() => [...new Map([design, ...designs].map((item) => [item.id, item])).values()], [design, designs]);
  const roleChoices = useMemo(() => {
    const values = (design.players ?? []).flatMap((player) => [player.position, player.role]).filter((value): value is string => Boolean(value));
    return ['coach', ...new Set(values)];
  }, [design.players]);
  const layoutChoices = kind === 'call_sheet'
    ? [{ value: 'table', label: 'Paginated call sheet table' }]
    : kind === 'wristband'
      ? [{ value: 'wristband_2col', label: 'Two-column wristband — standard' }, { value: 'wristband_3col', label: 'Three-column wristband — compact' }, { value: 'wristband_4col', label: 'Four-column wristband — sideline strip' }]
      : [{ value: 'single', label: 'One card per page' }, { value: 'grid_2x2', label: '2 × 2 packet grid' }, { value: 'grid_3x2', label: '3 × 2 packet grid' }];
  const exportDesignIds = singleDesignFormat ? [design.id] : (selectedDesignIds.length ? selectedDesignIds : [design.id]);
  const exportLayout = singleDesignFormat ? 'single' : layout;
  const preflightKey = useMemo(() => JSON.stringify({ designIds: exportDesignIds, kind, format, layout: exportLayout, role }), [exportDesignIds, kind, format, exportLayout, role]);

  useEffect(() => {
    setSelectedDesignIds([design.id]);
    setArtifact(null);
    setPreflight(null);
    setPreflightSignature('');
  }, [design.id]);
  useEffect(() => {
    setArtifact(null);
    setPreflight(null);
    setPreflightSignature('');
    setPreflightError('');
    setError('');
  }, [preflightKey, open]);

  const checkExport = async () => {
    if (!session) return;
    setPreflightBusy(true);
    setPreflightError('');
    try {
      const result = await preflightPlayDesignExport(session, exportDesignIds, kind, format, exportLayout, role);
      setPreflight(result);
      setPreflightSignature(preflightKey);
    } catch (failure) {
      setPreflight(null);
      setPreflightSignature('');
      setPreflightError(failure instanceof Error ? failure.message : 'Export preflight could not be completed.');
    } finally {
      setPreflightBusy(false);
    }
  };

  const generate = async () => {
    if (!session || !preflight || preflightSignature !== preflightKey || !preflight.can_render) return;
    setBusy(true);
    setError('');
    try {
      setArtifact(await exportPlayDesign(session, exportDesignIds, kind, format, blackWhite, exportLayout, role));
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Export could not be generated.');
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;
  const preflightReady = Boolean(preflight?.can_render && preflightSignature === preflightKey);

  return createPortal(
    <div className="modal-backdrop designer-modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="designer-export-dialog" role="dialog" aria-modal="true" aria-labelledby="designer-export-title">
        <button className="designer-dialog-close" type="button" aria-label="Close export dialog" onClick={onClose}><X size={18} /></button>
        <span className="designer-dialog-icon"><Download size={22} /></span>
        <p className="designer-kicker">Production output</p>
        <h2 id="designer-export-title">Export the canonical call</h2>
        <p>Server-rendered outputs include validation evidence, checksums, and organization branding.</p>
        <div className="export-dialog-grid">
          <label><span>Artifact</span><select ref={initialRef} value={kind} onChange={(event) => { const nextKind = event.target.value; setKind(nextKind); setLayout(defaultLayout(nextKind)); }}><option value="play_card">Play card</option><option value="call_sheet">Call sheet</option><option value="wristband">Wristband</option><option value="install_sheet">Install sheet</option></select></label>
          <label><span>Format</span><select value={format} onChange={(event) => { const next = event.target.value; setFormat(next); setSelectedDesignIds(next === 'svg' || next === 'png' ? [design.id] : selectedDesignIds); }}><option value="pdf">PDF</option><option value="svg">SVG</option><option value="png">PNG</option><option value="html">HTML</option><option value="json">JSON</option><option value="csv">CSV</option></select></label>
          <label><span>Packet layout</span><select disabled={singleDesignFormat} value={layout} onChange={(event) => setLayout(event.target.value)}>{layoutChoices.map((choice) => <option key={choice.value} value={choice.value}>{choice.label}</option>)}</select></label>
          <label><span>Audience view</span><select value={role} onChange={(event) => setRole(event.target.value)}>{roleChoices.map((value) => <option value={value} key={value}>{value === 'coach' ? 'Coach / staff — full call' : `${value} — focused view`}</option>)}</select></label>
          <label className="export-check"><input type="checkbox" checked={blackWhite} onChange={(event) => setBlackWhite(event.target.checked)} /> <span>Black-and-white copy-room mode</span></label>
        </div>
        {availableDesigns.length > 1 ? <label className="export-design-picker"><span>Designs in packet <small>{singleDesignFormat ? 'This format accepts one design.' : 'Ctrl/Cmd-click to select multiple.'}</small></span><select multiple size={Math.min(7, Math.max(3, availableDesigns.length))} value={singleDesignFormat ? [design.id] : selectedDesignIds} onChange={(event) => { const next = Array.from(event.target.selectedOptions).map((option) => option.value); setSelectedDesignIds(singleDesignFormat ? [design.id] : (next.length ? next : [design.id])); }}><option value={design.id}>{design.name || design.concept || design.id} · current</option>{availableDesigns.filter((item) => item.id !== design.id).map((item) => <option value={item.id} key={item.id}>{item.name || item.concept || item.id} · {item.unit} · v{item.version || '?'}</option>)}</select></label> : null}
        <p className="export-selection-summary" role="status">{exportDesignIds.length} design{exportDesignIds.length === 1 ? '' : 's'} selected for this {kind.replaceAll('_', ' ')}.</p>
        {error ? <p className="export-error" role="alert">{error}</p> : null}
        {preflightError ? <p className="export-error" role="alert">{preflightError}</p> : null}
        <section className={`export-preflight ${preflightReady ? 'is-valid' : preflight?.validation.status === 'invalid' ? 'is-invalid' : ''}`} aria-live="polite" aria-label="Export preflight">
          <div className="export-preflight__heading"><div><strong>Export preflight</strong><span>{preflightBusy ? 'Checking source records and legality…' : preflightReady ? 'Ready to render' : preflight?.validation.status === 'invalid' ? 'Blocked until issues are resolved' : 'Run a final check before rendering'}</span></div><button type="button" onClick={checkExport} disabled={preflightBusy || !session}>{preflightBusy ? <LoaderCircle className="spin" size={14} /> : <FileCheck2 size={14} />} {preflight ? 'Re-check' : 'Check export'}</button></div>
          {preflight ? <>
            <div className="export-preflight__stats"><span>{preflight.design_count} source play{preflight.design_count === 1 ? '' : 's'}</span><span>{preflight.page_count ?? 1} planned page{(preflight.page_count ?? 1) === 1 ? '' : 's'}</span><span>{preflight.page_size ?? 'letter'} · print layout</span><span>{preflight.source_lock?.status === 'locked' ? 'Source locked' : 'Source lock review'}</span><span>{preflight.validation.issues.length} note{preflight.validation.issues.length === 1 ? '' : 's'}</span><span>Manifest {preflight.source_manifest_hash.slice(0, 12)}…</span></div>
            {preflight.validation.issues.length ? <ul>{preflight.validation.issues.map((issue, index) => <li key={`${issue.code}-${issue.path}-${index}`}><strong>{issue.severity || 'note'}</strong><span>{issue.message}</span><small>{issue.path}</small></li>)}</ul> : <p className="export-preflight__clear">No export blockers found. The source lock will be attached to the artifact.</p>}
          </> : null}
        </section>
        {artifact ? <>
          <div className="export-result"><FileCheck2 size={22} /><div><strong>{artifact.filename}</strong><span>{artifact.bytes.toLocaleString()} bytes · {artifact.role || role} view · SHA-256 {artifact.sha256.slice(0, 14)}…</span><small className="export-result__quality">{artifact.integrity?.status === 'verified' ? 'Integrity verified' : 'Integrity review'} · {artifact.page_count ?? 1} page{(artifact.page_count ?? 1) === 1 ? '' : 's'} · {artifact.page_size ?? 'letter'} · {artifact.printer_safe ? 'printer-safe layout' : 'data export'} · {artifact.source_lock?.status === 'locked' ? 'source locked' : 'source lock review'}</small></div><button type="button" onClick={() => downloadArtifact(artifact)}><Download size={15} /> Download</button></div>
          {artifact.source_manifest?.length ? <div className="export-source-manifest" aria-label="Export source manifest"><header><strong>Source lock</strong><span>{artifact.source_manifest.length} play{artifact.source_manifest.length === 1 ? '' : 's'} · {artifact.source_manifest_hash?.slice(0, 14) ?? 'manifest'}…</span></header>{artifact.source_manifest.map((source) => <div key={source.design_id}><span>{source.name || source.design_id}</span><small>v{source.version || '?'} · {source.snapshot_id || 'no snapshot'} · {source.approval_state || source.status || 'draft'}</small></div>)}</div> : null}
        </> : null}
        <button className="button button--primary button--full" type="button" disabled={busy || !session || !preflightReady} onClick={generate}>{busy ? <LoaderCircle className="spin" size={17} /> : <FileCheck2 size={17} />} {busy ? 'Rendering…' : preflightReady ? 'Generate validated artifact' : 'Run preflight to unlock export'}</button>
      </section>
    </div>,
    document.body,
  );
}
