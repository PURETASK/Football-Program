import type { AppSession, UserRole } from '../types';

const STORAGE_KEY = 'nfl-fidos-app-session-v1';

interface TokenPayload {
  org?: string;
  role?: UserRole;
  sub?: string;
}

function decodeBase64Url(value: string): string {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/');
  return atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '='));
}

export function decodeTokenPayload(token: string): TokenPayload | null {
  try {
    const [payload] = token.split('.');
    if (!payload) return null;
    return JSON.parse(decodeBase64Url(payload)) as TokenPayload;
  } catch {
    return null;
  }
}

export function createSession(organizationId: string, token: string): AppSession {
  const payload = decodeTokenPayload(token.trim());
  return {
    organizationId: organizationId.trim(),
    token: token.trim(),
    role: payload?.role ?? 'coach_staff',
    subject: payload?.sub,
  };
}

export function readStoredSession(): AppSession | null {
  try {
    const value = sessionStorage.getItem(STORAGE_KEY);
    if (!value) return null;
    const parsed = JSON.parse(value) as Partial<AppSession>;
    if (!parsed.organizationId || !parsed.token || !parsed.role) return null;
    return parsed as AppSession;
  } catch {
    return null;
  }
}

export function storeSession(session: AppSession | null): void {
  if (session) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } else {
    sessionStorage.removeItem(STORAGE_KEY);
  }
}
