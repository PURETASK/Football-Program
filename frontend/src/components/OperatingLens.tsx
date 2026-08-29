import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, UsersRound, X } from 'lucide-react';
import { createPortal } from 'react-dom';

import { useModalFocusTrap } from '../hooks/useModalFocusTrap';

export const OPERATING_LENSES = [
  { key: 'head-coach', label: 'Head coach', description: 'Program-wide decisions, readiness, approvals, and delivery.' },
  { key: 'offensive-coordinator', label: 'Offensive coordinator', description: 'Offense, protection, install, and offensive game-plan work.' },
  { key: 'defensive-coordinator', label: 'Defensive coordinator', description: 'Fronts, coverages, pressure, fits, and defensive teaching.' },
  { key: 'position-coach', label: 'Position coach', description: 'Position-group assignments, teaching, and player readiness.' },
  { key: 'analyst', label: 'Analyst', description: 'Evidence, tendencies, validation, and outcome analysis.' },
] as const;

const STORAGE_KEY = 'nfl-fidos-operating-lens-v1';

export function OperatingLens({ open, onClose, value, onChange }: { open: boolean; onClose: () => void; value: string; onChange: (value: string) => void }) {
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  useModalFocusTrap(open, dialogRef, closeRef, onClose);
  if (!open) return null;
  return createPortal(
    <div className="modal-backdrop workspace-tutorial-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="workspace-tutorial operating-lens" role="dialog" aria-modal="true" aria-labelledby="operating-lens-title">
        <header className="workspace-tutorial__header">
          <span className="workspace-tutorial__icon" aria-hidden="true"><UsersRound size={21} /></span>
          <div><p>Workspace scope</p><strong id="operating-lens-title">Choose your operating lens</strong></div>
          <button ref={closeRef} className="icon-button" type="button" aria-label="Close operating lens" onClick={onClose}><X size={18} /></button>
        </header>
        <div className="workspace-tutorial__intro"><UsersRound size={15} /><span>This filters the working perspective and guidance. It does not grant permissions or change API authorization.</span></div>
        <div className="operating-lens__options">
          {OPERATING_LENSES.map((lens) => <button key={lens.key} className={lens.key === value ? 'operating-lens__option is-selected' : 'operating-lens__option'} type="button" onClick={() => { onChange(lens.key); onClose(); }}><span><strong>{lens.label}</strong><small>{lens.description}</small></span>{lens.key === value ? <Check size={18} aria-label="Selected" /> : null}</button>)}
        </div>
      </section>
    </div>,
    document.body,
  );
}

export function useOperatingLens() {
  const [value, setValue] = useState('head-coach');
  useEffect(() => {
    const stored = window.sessionStorage.getItem(STORAGE_KEY);
    if (stored && OPERATING_LENSES.some((lens) => lens.key === stored)) setValue(stored);
  }, []);
  const update = (next: string) => {
    if (!OPERATING_LENSES.some((lens) => lens.key === next)) return;
    setValue(next);
    window.sessionStorage.setItem(STORAGE_KEY, next);
  };
  return { value, update, label: OPERATING_LENSES.find((lens) => lens.key === value)?.label ?? 'Head coach' };
}

export function OperatingLensButton({ label, onClick }: { label: string; onClick: () => void }) {
  return <button className="operating-lens-button" type="button" onClick={onClick} aria-label={`Operating lens: ${label}`} title="Change operating lens"><UsersRound size={15} /><span>{label}</span><ChevronDown size={14} /></button>;
}
