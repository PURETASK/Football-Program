import { useEffect, useMemo, useRef, useState, type ComponentType } from 'react';
import { createPortal } from 'react-dom';
import { ArrowRight, BookOpenText, Search, X } from 'lucide-react';
import { Link } from 'react-router-dom';

import { usePlayDesignsQuery } from '../hooks/useWorkspaceData';
import { useModalFocusTrap } from '../hooks/useModalFocusTrap';
import { playDisplayName } from './PlayCard';

interface CommandNavigationItem {
  label: string;
  path: string;
  icon: ComponentType<{ size?: number; 'aria-hidden'?: boolean }>;
}

export function CommandPalette({
  open,
  onClose,
  navigation,
}: {
  open: boolean;
  onClose: () => void;
  navigation: CommandNavigationItem[];
}) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const playsQuery = usePlayDesignsQuery();

  useModalFocusTrap(open, dialogRef, inputRef, onClose);

  useEffect(() => {
    if (!open) return undefined;
    setQuery('');
    return undefined;
  }, [open]);

  const normalized = query.trim().toLowerCase();
  const matchingNavigation = useMemo(
    () => navigation.filter((item) => !normalized || item.label.toLowerCase().includes(normalized)),
    [navigation, normalized],
  );
  const matchingPlays = useMemo(
    () => (playsQuery.data ?? []).filter((play) => {
      const text = [playDisplayName(play), play.id, play.formation, play.personnel, play.unit].filter(Boolean).join(' ').toLowerCase();
      return !normalized || text.includes(normalized);
    }).slice(0, 5),
    [normalized, playsQuery.data],
  );

  if (!open) return null;

  return createPortal(
    <div className="modal-backdrop command-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="command-palette" role="dialog" aria-modal="true" aria-labelledby="command-title">
        <h2 className="sr-only" id="command-title">Command search</h2>
        <label className="command-palette__search">
          <Search size={20} aria-hidden="true" />
          <span className="sr-only">Search navigation and plays</span>
          <input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search plays or jump to a workspace…" />
          <button type="button" aria-label="Close command search" onClick={onClose}><X size={18} /></button>
        </label>
        <div className="command-palette__results">
          {matchingNavigation.length ? (
            <section aria-labelledby="command-workspaces">
              <p id="command-workspaces">Workspaces</p>
              <div>
                {matchingNavigation.map(({ label, path, icon: Icon }) => (
                  <Link key={path} to={path} onClick={onClose}>
                    <span><Icon aria-hidden size={17} /></span>
                    <strong>{label}</strong>
                    <ArrowRight aria-hidden="true" size={15} />
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
          {matchingPlays.length ? (
            <section aria-labelledby="command-plays">
              <p id="command-plays">Playbook</p>
              <div>
                {matchingPlays.map((play) => (
                  <Link to={`/playbook/designer/${encodeURIComponent(play.id)}`} key={play.id} onClick={onClose}>
                    <span><BookOpenText aria-hidden="true" size={17} /></span>
                    <strong>{playDisplayName(play)} <small>{play.personnel || 'Open'} · {play.unit}</small></strong>
                    <ArrowRight aria-hidden="true" size={15} />
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
          {!matchingNavigation.length && !matchingPlays.length ? (
            <div className="command-palette__empty"><Search size={24} /><strong>No matches</strong><span>Try a concept, formation, or workspace name.</span></div>
          ) : null}
        </div>
        <footer><span><kbd>Tab</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></footer>
      </section>
    </div>,
    document.body,
  );
}
