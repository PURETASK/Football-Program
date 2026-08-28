import { createSession, decodeTokenPayload, readStoredSession, storeSession } from './session';

function encodedToken(payload: Record<string, string>): string {
  const encoded = btoa(JSON.stringify(payload)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
  return `${encoded}.signature`;
}

describe('session helpers', () => {
  it('decodes organization, role, and subject from the signed-token payload', () => {
    const token = encodedToken({ org: 'ORG-DEMO', role: 'program_owner', sub: 'DEMO-COACH' });
    expect(decodeTokenPayload(token)).toEqual({ org: 'ORG-DEMO', role: 'program_owner', sub: 'DEMO-COACH' });
    expect(createSession('ORG-DEMO', token)).toMatchObject({ organizationId: 'ORG-DEMO', role: 'program_owner', subject: 'DEMO-COACH' });
  });

  it('stores credentials in session storage only for the current tab', () => {
    const session = createSession('ORG-DEMO', encodedToken({ org: 'ORG-DEMO', role: 'coach_staff' }));
    storeSession(session);
    expect(readStoredSession()).toEqual(session);
    expect(localStorage.length).toBe(0);
    storeSession(null);
    expect(readStoredSession()).toBeNull();
  });

  it('fails closed for malformed token payloads', () => {
    expect(decodeTokenPayload('not-a-token')).toBeNull();
  });
});
