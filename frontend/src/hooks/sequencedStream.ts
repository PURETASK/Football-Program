/** Keep replayable SSE consumers monotonic when a transport duplicates or reorders events. */
export function acceptSequencedEvent(cursor: number, incoming?: number, requireContiguous = true): { accepted: boolean; nextCursor: number; reason: 'accepted' | 'duplicate' | 'gap' | 'unsequenced' } {
  if (incoming === undefined || !Number.isFinite(incoming)) return { accepted: true, nextCursor: cursor, reason: 'unsequenced' };
  if (incoming <= cursor) return { accepted: false, nextCursor: cursor, reason: 'duplicate' };
  if (requireContiguous && cursor > 0 && incoming !== cursor + 1) return { accepted: false, nextCursor: cursor, reason: 'gap' };
  return { accepted: true, nextCursor: incoming, reason: 'accepted' };
}

/** Decide whether a stream consumer can continue or must replay from its cursor. */
export function sequenceRecoveryAction(result: ReturnType<typeof acceptSequencedEvent>): 'accept' | 'ignore' | 'reconnect' {
  if (result.accepted) return 'accept';
  return result.reason === 'gap' ? 'reconnect' : 'ignore';
}
