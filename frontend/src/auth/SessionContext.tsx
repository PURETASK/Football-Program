import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

import { readStoredSession, storeSession } from '../lib/session';
import type { AppSession } from '../types';

interface SessionContextValue {
  session: AppSession | null;
  setSession: (session: AppSession) => void;
  clearSession: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, updateSession] = useState<AppSession | null>(() => readStoredSession());

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      setSession: (nextSession) => {
        storeSession(nextSession);
        updateSession(nextSession);
      },
      clearSession: () => {
        storeSession(null);
        updateSession(null);
      },
    }),
    [session],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSession must be used inside SessionProvider');
  return context;
}
