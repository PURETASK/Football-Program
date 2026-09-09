import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, ClipboardPenLine, ShieldCheck, X } from 'lucide-react';
import { createPortal } from 'react-dom';

import { useModalFocusTrap } from '../hooks/useModalFocusTrap';
import { createOrganizationContext } from '../lib/api';
import type { AppSession } from '../types';

const SETUP_DRAFT_KEY = 'nfl-fidos-coach-setup-draft-v1';

interface SetupDraft {
  name: string;
  teamId: string;
  season: string;
  ruleProfile: string;
  terminologyVersion: string;
  people: string;
}

const DEFAULT_DRAFT: SetupDraft = {
  name: 'Demo Football Program',
  teamId: 'TEAM-DEMO-2026',
  season: '2026',
  ruleProfile: 'nfl',
  terminologyVersion: 'coach-terminology-v1',
  people: 'Jordan Coach|head_coach|HC\nTaylor Coordinator|offensive_coordinator|OC\nCasey Defender|defensive_coordinator|DC\nDemo Quarterback|player|QB',
};

function loadDraft(): SetupDraft {
  try {
    const saved = JSON.parse(window.localStorage.getItem(SETUP_DRAFT_KEY) || 'null');
    return saved && typeof saved === 'object' ? { ...DEFAULT_DRAFT, ...saved } : DEFAULT_DRAFT;
  } catch { return DEFAULT_DRAFT; }
}

function parsePeople(value: string): Array<Record<string, unknown>> {
  return value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map((line, index) => {
    const [name, role = 'staff', position = ''] = line.split('|').map((item) => item.trim());
    return { id: `SETUP-PERSON-${index + 1}`, name, type: role === 'player' ? 'player' : 'staff', role, position };
  });
}

const STEPS = [
  { label: 'Program', title: 'Name the program', description: 'This creates a draft organization context. It does not activate production or advance Stage 0.' },
  { label: 'Season', title: 'Set the football context', description: 'Choose the season, team identity, rule profile, and terminology package the workspaces should use.' },
  { label: 'People', title: 'Add your first staff and roster records', description: 'Use one person per line in the format Name|role|position. This is a starter context; full roster management stays in Roster & Personnel.' },
  { label: 'Review', title: 'Review before creating', description: 'The setup creates an organization-scoped draft through the authoritative API when a connected owner session is available.' },
];

export function CoachSetupWizard({ open, onClose, session, onCreated }: { open: boolean; onClose: () => void; session?: AppSession; onCreated?: () => void }) {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<SetupDraft>(DEFAULT_DRAFT);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);
  const dialogRef = useRef<HTMLElement>(null);
  const firstRef = useRef<HTMLInputElement>(null);
  useModalFocusTrap(open, dialogRef, firstRef, onClose);

  useEffect(() => { if (open) { setStep(0); setDraft(loadDraft()); setError(''); setSuccess(''); } }, [open]);
  if (!open) return null;
  const current = STEPS[step];
  const update = (field: keyof SetupDraft, value: string) => setDraft((previous) => ({ ...previous, [field]: value }));
  const next = () => { window.localStorage.setItem(SETUP_DRAFT_KEY, JSON.stringify(draft)); setError(''); setStep((value) => Math.min(STEPS.length - 1, value + 1)); };
  const submit = async () => {
    window.localStorage.setItem(SETUP_DRAFT_KEY, JSON.stringify(draft));
    if (!session) { setError('Connect an owner organization session before creating the organization context. Your setup draft is saved in this browser.'); return; }
    setSaving(true); setError('');
    try {
      await createOrganizationContext(session, { name: draft.name, teamId: draft.teamId, season: draft.season, ruleProfile: draft.ruleProfile, terminologyVersion: draft.terminologyVersion, people: parsePeople(draft.people) });
      setSuccess('Draft organization context created. Review and approve it from Admin & Governance.');
      onCreated?.();
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'The organization context could not be created.'); }
    finally { setSaving(false); }
  };
  return createPortal(
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="coach-setup" role="dialog" aria-modal="true" aria-labelledby="coach-setup-title" aria-describedby="coach-setup-description">
        <header className="coach-setup__header"><span className="workspace-tutorial__icon" aria-hidden="true"><ClipboardPenLine size={21} /></span><div><p>Head coach setup</p><strong id="coach-setup-title">Build your program context</strong></div><button className="icon-button" type="button" aria-label="Close coach setup" onClick={onClose}><X size={18} /></button></header>
        <div className="coach-setup__progress" aria-label={`Setup step ${step + 1} of ${STEPS.length}`}>{STEPS.map((item, index) => <span className={index === step ? 'is-active' : index < step ? 'is-complete' : ''} key={item.label}><b>{index < step ? <Check size={13} /> : index + 1}</b>{item.label}</span>)}</div>
        <div className="coach-setup__body"><p className="eyebrow">Step {step + 1} · {current.label}</p><h2>{current.title}</h2><p id="coach-setup-description">{current.description}</p>
          {step === 0 ? <div className="coach-setup__grid"><label><span>Program name</span><input ref={firstRef} value={draft.name} onChange={(event) => update('name', event.target.value)} required /></label><label><span>Team ID</span><input value={draft.teamId} onChange={(event) => update('teamId', event.target.value)} required /></label></div> : null}
          {step === 1 ? <div className="coach-setup__grid"><label><span>Season</span><input inputMode="numeric" value={draft.season} onChange={(event) => update('season', event.target.value)} required /></label><label><span>Rule profile</span><select value={draft.ruleProfile} onChange={(event) => update('ruleProfile', event.target.value)}><option value="nfl">NFL</option><option value="ncaa">NCAA</option><option value="high_school">High school</option><option value="youth">Youth</option><option value="flag">Flag</option></select></label><label className="is-wide"><span>Terminology version</span><input value={draft.terminologyVersion} onChange={(event) => update('terminologyVersion', event.target.value)} /></label></div> : null}
          {step === 2 ? <label className="coach-setup__people"><span>People roster <small>Name|role|position</small></span><textarea rows={8} value={draft.people} onChange={(event) => update('people', event.target.value)} /></label> : null}
          {step === 3 ? <div className="coach-setup__review"><div><strong>{draft.name}</strong><span>{draft.teamId} · {draft.season} · {draft.ruleProfile.toUpperCase()}</span></div><div><strong>{parsePeople(draft.people).length} people</strong><span>{draft.terminologyVersion}</span></div><p><ShieldCheck size={15} /> This remains a draft until an authorized owner reviews and approves it in Admin & Governance.</p></div> : null}
          {error ? <p className="form-error" role="alert">{error}</p> : null}{success ? <p className="form-success" role="status">{success}</p> : null}
        </div>
        <footer className="coach-setup__footer"><button className="button button--quiet" type="button" disabled={step === 0 || saving} onClick={() => setStep((value) => Math.max(0, value - 1))}><ArrowLeft size={15} /> Back</button><span>{step + 1} of {STEPS.length}</span>{step < STEPS.length - 1 ? <button className="button button--primary" type="button" onClick={next}>Continue <ArrowRight size={15} /></button> : <button className="button button--primary" type="button" disabled={saving || Boolean(success)} onClick={() => void submit()}>{saving ? 'Creating…' : 'Create draft context'} <Check size={15} /></button>}</footer>
      </section>
    </div>,
    document.body,
  );
}
