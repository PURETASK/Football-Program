import type { AppSession } from '../types';
import { clearEncryptedOfflineCache, readEncryptedOfflineCache, writeEncryptedOfflineCache } from './encryptedOfflineCache';

export type CollaborationOutboxAction =
  | { id: string; kind: 'thread'; payload: { threadId: string; title: string; body: string; entityType: string; entityId: string; deepLink: string; assignee?: string; mentions?: string[]; participants?: string[]; priority?: string; dueAt?: string }; createdAt: string; attempts: number; lastError?: string }
  | { id: string; kind: 'comment'; payload: { threadId: string; commentId: string; body: string; mentions?: string[] }; createdAt: string; attempts: number; lastError?: string }
  | { id: string; kind: 'assign'; payload: { threadId: string; assignee: string; dueAt?: string; priority?: string }; createdAt: string; attempts: number; lastError?: string }
  | { id: string; kind: 'resolve'; payload: { threadId: string; decision: 'resolved' | 'reopened'; rationale: string }; createdAt: string; attempts: number; lastError?: string }
  | { id: string; kind: 'mark_notifications_read'; payload: { notificationIds: string[] }; createdAt: string; attempts: number; lastError?: string };

const SCOPE_KEY = 'collaboration-outbox-v1';

export async function readCollaborationOutbox(session: AppSession): Promise<CollaborationOutboxAction[]> {
  const cached = await readEncryptedOfflineCache<CollaborationOutboxAction[]>(session, SCOPE_KEY);
  if (!cached || !Array.isArray(cached.value)) return [];
  return cached.value.filter((action) => Boolean(action?.id && action?.kind && action?.payload));
}

export async function writeCollaborationOutbox(session: AppSession, actions: CollaborationOutboxAction[]): Promise<boolean> {
  if (!actions.length) {
    clearEncryptedOfflineCache(session, SCOPE_KEY);
    return true;
  }
  return writeEncryptedOfflineCache(session, SCOPE_KEY, actions, { action_count: actions.length });
}

export async function enqueueCollaborationAction(session: AppSession, action: Omit<CollaborationOutboxAction, 'createdAt' | 'attempts'>): Promise<CollaborationOutboxAction[]> {
  const current = await readCollaborationOutbox(session);
  if (current.some((candidate) => candidate.id === action.id)) return current;
  const next: CollaborationOutboxAction[] = [...current, { ...action, createdAt: new Date().toISOString(), attempts: 0 } as CollaborationOutboxAction];
  if (!await writeCollaborationOutbox(session, next)) throw new Error('Secure offline outbox storage is unavailable. Keep this window open and retry when storage is available.');
  return next;
}

export async function removeCollaborationAction(session: AppSession, actionId: string): Promise<CollaborationOutboxAction[]> {
  const next = (await readCollaborationOutbox(session)).filter((action) => action.id !== actionId);
  if (!await writeCollaborationOutbox(session, next)) throw new Error('Secure offline outbox could not acknowledge the delivered action. Retry reconciliation before sending more actions.');
  return next;
}

export async function markCollaborationActionFailed(session: AppSession, action: CollaborationOutboxAction, error: unknown): Promise<CollaborationOutboxAction[]> {
  const current = await readCollaborationOutbox(session);
  const next = current.map((candidate) => candidate.id === action.id
    ? { ...candidate, attempts: candidate.attempts + 1, lastError: error instanceof Error ? error.message : 'Temporary synchronization failure.' }
    : candidate);
  if (!await writeCollaborationOutbox(session, next)) throw new Error('Secure offline outbox could not persist retry evidence. Keep this window open and retry.');
  return next;
}
