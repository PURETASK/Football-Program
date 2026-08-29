import { describe, expect, it } from 'vitest';
import { acceptSequencedEvent, sequenceRecoveryAction } from './sequencedStream';

describe('sequenced collaboration stream', () => {
  it('accepts the next event and advances the replay cursor', () => {
    expect(acceptSequencedEvent(4, 5)).toEqual({ accepted: true, nextCursor: 5, reason: 'accepted' });
  });

  it('ignores duplicates without regressing the cursor', () => {
    expect(acceptSequencedEvent(5, 5)).toEqual({ accepted: false, nextCursor: 5, reason: 'duplicate' });
    expect(acceptSequencedEvent(5, 3)).toEqual({ accepted: false, nextCursor: 5, reason: 'duplicate' });
  });

  it('holds an out-of-order event so reconnect replay can request the missing sequence', () => {
    const result = acceptSequencedEvent(5, 7);
    expect(result).toEqual({ accepted: false, nextCursor: 5, reason: 'gap' });
    expect(sequenceRecoveryAction(result)).toBe('reconnect');
  });

  it('allows legitimate gaps for role-filtered organization streams', () => {
    const result = acceptSequencedEvent(5, 7, false);
    expect(result).toEqual({ accepted: true, nextCursor: 7, reason: 'accepted' });
    expect(sequenceRecoveryAction(result)).toBe('accept');
  });

  it('ignores duplicates without forcing an unnecessary reconnect', () => {
    expect(sequenceRecoveryAction(acceptSequencedEvent(5, 5))).toBe('ignore');
  });
});
