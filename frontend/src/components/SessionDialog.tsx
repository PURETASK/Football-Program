import { useRef, useState, type FormEvent } from 'react';
import { createPortal } from 'react-dom';
import { KeyRound, ShieldCheck, X } from 'lucide-react';

import { useSession } from '../auth/SessionContext';
import { createSession, decodeTokenPayload } from '../lib/session';
import { useModalFocusTrap } from '../hooks/useModalFocusTrap';

export function SessionDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { session, setSession, clearSession } = useSession();
  const [organizationId, setOrganizationId] = useState(session?.organizationId ?? 'ORG-DEMO-FIDOS-001');
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const organizationRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  useModalFocusTrap(open, dialogRef, organizationRef, onClose);

  if (!open) return null;

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const payload = decodeTokenPayload(token.trim());
    if (!organizationId.trim() || !token.trim()) {
      setError('Organization and Bearer token are required.');
      return;
    }
    if (!payload) {
      setError('The token format could not be read. Issue a fresh local token and try again.');
      return;
    }
    if (payload.org && payload.org !== organizationId.trim()) {
      setError(`This token belongs to ${payload.org}, not ${organizationId.trim()}.`);
      return;
    }
    setSession(createSession(organizationId, token));
    setToken('');
    setError('');
    onClose();
  };

  return createPortal(
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section ref={dialogRef} className="session-dialog" role="dialog" aria-labelledby="session-title" aria-modal="true">
        <button className="icon-button session-dialog__close" type="button" aria-label="Close team access dialog" onClick={onClose}>
          <X size={19} />
        </button>
        <span className="session-dialog__icon" aria-hidden="true">
          <KeyRound size={24} />
        </span>
        <p className="eyebrow">Secure team access</p>
        <h2 id="session-title">Connect your organization</h2>
        <p className="session-dialog__intro">
          Use an organization-scoped token. It stays in this browser tab and is never added to the application bundle.
        </p>
        <form className="session-form" onSubmit={handleSubmit}>
          <label>
            Organization ID
            <input
              ref={organizationRef}
              autoComplete="organization"
              onChange={(event) => setOrganizationId(event.target.value)}
              placeholder="ORG-..."
              value={organizationId}
            />
          </label>
          <label>
            Bearer token
            <textarea
              autoComplete="off"
              onChange={(event) => setToken(event.target.value)}
              placeholder="Paste a signed organization token"
              rows={4}
              value={token}
            />
          </label>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          <button className="button button--primary button--full" type="submit">
            <ShieldCheck size={17} />
            Connect securely
          </button>
        </form>
        {session ? (
          <button
            className="button button--quiet button--full"
            type="button"
            onClick={() => {
              clearSession();
              setToken('');
              onClose();
            }}
          >
            Disconnect {session.organizationId}
          </button>
        ) : null}
      </section>
    </div>,
    document.body,
  );
}
