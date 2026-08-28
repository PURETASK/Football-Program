import type { AppSession } from '../types';
import { clearEncryptedOfflineCache, readEncryptedOfflineCache, writeEncryptedOfflineCache } from './encryptedOfflineCache';
import { enqueueCollaborationAction, markCollaborationActionFailed, readCollaborationOutbox, removeCollaborationAction, writeCollaborationOutbox } from './collaborationOutbox';

const SESSION: AppSession = { organizationId: 'ORG-OUTBOX', token: 'outbox-token', role: 'coach_staff', subject: 'COACH-1' };

describe('collaboration outbox', () => {
  beforeEach(() => {
    clearEncryptedOfflineCache(SESSION, 'collaboration-outbox-v1');
  });

  it('stores organization-scoped actions without exposing plaintext payloads', async () => {
    await enqueueCollaborationAction(SESSION, {
      id: 'OUTBOX-THREAD-1',
      kind: 'thread',
      payload: { threadId: 'COLLAB-THREAD-1', title: 'Pressure answer', body: 'Review the clip.', entityType: 'game_plan', entityId: 'GAMEPLAN-1', deepLink: '/game-plan' },
    });
    const raw = localStorage.getItem('nfl-fidos-offline-cache-v1:ORG-OUTBOX:collaboration-outbox-v1');
    expect(raw).toBeTruthy();
    expect(raw).not.toContain('Pressure answer');
    expect((await readCollaborationOutbox(SESSION))[0]).toMatchObject({ id: 'OUTBOX-THREAD-1', kind: 'thread', attempts: 0 });
  });

  it('deduplicates actions and removes them after acknowledged delivery', async () => {
    const action = { id: 'OUTBOX-COMMENT-1', kind: 'comment' as const, payload: { threadId: 'COLLAB-THREAD-1', commentId: 'COMMENT-1', body: 'Evidence attached.' } };
    await enqueueCollaborationAction(SESSION, action);
    await enqueueCollaborationAction(SESSION, action);
    expect((await readCollaborationOutbox(SESSION)).length).toBe(1);
    await removeCollaborationAction(SESSION, action.id);
    expect(await readCollaborationOutbox(SESSION)).toEqual([]);
  });

  it('increments retry evidence while preserving the action for reconnect', async () => {
    const action = { id: 'OUTBOX-ASSIGN-1', kind: 'assign' as const, payload: { threadId: 'COLLAB-THREAD-1', assignee: 'COACH-2', priority: 'high' } };
    await enqueueCollaborationAction(SESSION, action);
    const stored = (await readCollaborationOutbox(SESSION))[0];
    await markCollaborationActionFailed(SESSION, stored, new Error('network unavailable'));
    expect((await readCollaborationOutbox(SESSION))[0]).toMatchObject({ attempts: 1, lastError: 'network unavailable' });
  });

  it('clears the encrypted cache when the outbox becomes empty', async () => {
    await writeCollaborationOutbox(SESSION, []);
    expect(await readEncryptedOfflineCache(SESSION, 'collaboration-outbox-v1')).toBeNull();
  });
});
