import type { AppSession, PlayDesign } from '../types';
import { clearEncryptedOfflineCache, readEncryptedOfflineCache, writeEncryptedOfflineCache } from './encryptedOfflineCache';

export interface OfflineDraftRecovery {
  design: PlayDesign;
  updatedAt: string;
  baseRevision?: number;
}

function scopeKey(designId: string): string {
  return `play-draft:${designId}`;
}

export async function writeOfflineDraft(session: AppSession, design: PlayDesign): Promise<boolean> {
  return writeEncryptedOfflineCache(session, scopeKey(design.id), design, { design_id: design.id, base_revision: design._revision });
}

export async function readOfflineDraft(session: AppSession, designId: string): Promise<OfflineDraftRecovery | null> {
  const cached = await readEncryptedOfflineCache<PlayDesign>(session, scopeKey(designId));
  if (!cached || cached.value.id !== designId) return null;
  return { design: cached.value, updatedAt: cached.updatedAt, baseRevision: typeof cached.metadata.base_revision === 'number' ? cached.metadata.base_revision : cached.value._revision };
}

export function clearOfflineDraft(session: AppSession, designId: string): void {
  clearEncryptedOfflineCache(session, scopeKey(designId));
}
