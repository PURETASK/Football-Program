import { beforeEach, describe, expect, it } from 'vitest';

import type { AppSession } from '../types';
import { clearEncryptedOfflineCache, readEncryptedOfflineCache, writeEncryptedOfflineCache } from './encryptedOfflineCache';

const SESSION: AppSession = { organizationId: 'ORG-CACHE-1', token: 'session-token', role: 'player', subject: 'PLAYER-1' };

describe('session-bound encrypted offline cache', () => {
  beforeEach(() => localStorage.clear());

  it('never stores raw player learning records and rejects a different token', async () => {
    const value = { privacy: 'approved-only', assignments: [{ id: 'ASSIGNMENT-1', title: 'Dagger' }] };
    expect(await writeEncryptedOfflineCache(SESSION, 'player-today:PLAYER-1', value, { approved_only: true })).toBe(true);
    const raw = localStorage.getItem('nfl-fidos-offline-cache-v1:ORG-CACHE-1:player-today%3APLAYER-1');
    expect(raw).toBeTruthy();
    expect(raw).not.toContain('Dagger');
    expect((await readEncryptedOfflineCache<typeof value>(SESSION, 'player-today:PLAYER-1'))?.value).toEqual(value);
    expect(await readEncryptedOfflineCache({ ...SESSION, token: 'rotated-token' }, 'player-today:PLAYER-1')).toBeNull();
  });

  it('clears the scoped cache entry', async () => {
    await writeEncryptedOfflineCache(SESSION, 'player-today:PLAYER-1', { ok: true });
    clearEncryptedOfflineCache(SESSION, 'player-today:PLAYER-1');
    expect(await readEncryptedOfflineCache(SESSION, 'player-today:PLAYER-1')).toBeNull();
  });
});
