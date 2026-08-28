import type { AppSession } from '../types';

const STORAGE_PREFIX = 'nfl-fidos-offline-cache-v1:';
const ENVELOPE_VERSION = 1;

export interface EncryptedOfflineCacheResult<T> {
  value: T;
  metadata: Record<string, unknown>;
}

interface EncryptedCacheEnvelope {
  version: number;
  organization_id: string;
  scope_key: string;
  updated_at: string;
  metadata: Record<string, unknown>;
  iv: string;
  ciphertext: string;
}

function storageKey(session: AppSession, scopeKey: string): string {
  return `${STORAGE_PREFIX}${encodeURIComponent(session.organizationId)}:${encodeURIComponent(scopeKey)}`;
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

async function encryptionKey(session: AppSession): Promise<CryptoKey | null> {
  const cryptoApi = globalThis.crypto;
  if (!cryptoApi?.subtle) return null;
  const encoder = new TextEncoder();
  const material = await cryptoApi.subtle.importKey('raw', encoder.encode(`${session.organizationId}:${session.token}`), 'PBKDF2', false, ['deriveKey']);
  return cryptoApi.subtle.deriveKey(
    { name: 'PBKDF2', salt: encoder.encode(`nfl-fidos-offline-cache:${session.organizationId}`), iterations: 100_000, hash: 'SHA-256' },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  );
}

export async function writeEncryptedOfflineCache<T>(session: AppSession, scopeKey: string, value: T, metadata: Record<string, unknown> = {}): Promise<boolean> {
  try {
    const key = await encryptionKey(session);
    if (!key) return false;
    const cryptoApi = globalThis.crypto;
    const iv = cryptoApi.getRandomValues(new Uint8Array(12));
    const plaintext = new TextEncoder().encode(JSON.stringify(value));
    const encrypted = await cryptoApi.subtle.encrypt({ name: 'AES-GCM', iv }, key, plaintext);
    const envelope: EncryptedCacheEnvelope = {
      version: ENVELOPE_VERSION,
      organization_id: session.organizationId,
      scope_key: scopeKey,
      updated_at: new Date().toISOString(),
      metadata,
      iv: bytesToBase64(iv),
      ciphertext: bytesToBase64(new Uint8Array(encrypted)),
    };
    localStorage.setItem(storageKey(session, scopeKey), JSON.stringify(envelope));
    return true;
  } catch {
    return false;
  }
}

export async function readEncryptedOfflineCache<T>(session: AppSession, scopeKey: string): Promise<(EncryptedOfflineCacheResult<T> & { updatedAt: string }) | null> {
  try {
    const raw = localStorage.getItem(storageKey(session, scopeKey));
    if (!raw) return null;
    const envelope = JSON.parse(raw) as EncryptedCacheEnvelope;
    if (envelope.version !== ENVELOPE_VERSION || envelope.organization_id !== session.organizationId || envelope.scope_key !== scopeKey) return null;
    const key = await encryptionKey(session);
    if (!key) return null;
    const plaintext = await globalThis.crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: base64ToBytes(envelope.iv) as unknown as BufferSource },
      key,
      base64ToBytes(envelope.ciphertext) as unknown as BufferSource,
    );
    return { value: JSON.parse(new TextDecoder().decode(plaintext)) as T, metadata: envelope.metadata ?? {}, updatedAt: envelope.updated_at };
  } catch {
    return null;
  }
}

export function clearEncryptedOfflineCache(session: AppSession, scopeKey: string): void {
  try {
    localStorage.removeItem(storageKey(session, scopeKey));
  } catch {
    // Storage policies can make cleanup unavailable; expiry/rotation will invalidate the ciphertext.
  }
}
