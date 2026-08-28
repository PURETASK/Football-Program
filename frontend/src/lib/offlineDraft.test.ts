import { beforeEach, describe, expect, it } from 'vitest';

import type { AppSession, PlayDesign } from '../types';
import { clearOfflineDraft, readOfflineDraft, writeOfflineDraft } from './offlineDraft';

const SESSION: AppSession = { organizationId: 'ORG-OFFLINE-1', token: 'session-token', role: 'coach_staff', subject: 'COACH-1' };
const DESIGN: PlayDesign = { id: 'PLAY-OFFLINE-1', unit: 'offense', name: 'Secure Dagger', _revision: 4, players: [], elements: [] };

describe('encrypted offline play drafts', () => {
  beforeEach(() => localStorage.clear());

  it('stores ciphertext and recovers the draft only with the same authorized session', async () => {
    const stored = await writeOfflineDraft(SESSION, DESIGN);
    expect(stored).toBe(true);
    expect(localStorage.length).toBe(1);
    expect(localStorage.getItem('nfl-fidos-offline-cache-v1:ORG-OFFLINE-1:play-draft%3APLAY-OFFLINE-1')).not.toContain('Secure dagger');

    const recovered = await readOfflineDraft(SESSION, DESIGN.id);
    expect(recovered?.design).toEqual(DESIGN);
    expect(recovered?.baseRevision).toBe(4);
    expect(await readOfflineDraft({ ...SESSION, token: 'different-token' }, DESIGN.id)).toBeNull();
  });

  it('clears a recovered draft after a successful save', async () => {
    await writeOfflineDraft(SESSION, DESIGN);
    clearOfflineDraft(SESSION, DESIGN.id);
    expect(await readOfflineDraft(SESSION, DESIGN.id)).toBeNull();
  });
});
