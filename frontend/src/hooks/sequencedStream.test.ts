import { describe, expect, it } from 'vitest';
import { acceptSequencedEvent } from './sequencedStream';

describe('sequenced collaboration stream', () => {
  it('accepts the next event and advances the replay cursor', () => {
    expect(acceptSequencedEvent(4, 5)).toEqual({ accepted: true, nextCursor: 5, reason: 'accepted' });
  });

  it('ignores duplicates without regressing the cursor', () => {
    expect(acceptSequencedEvent(5, 5)).toEqual({ accepted: false, nextCursor: 5, reason: 'duplicate' });
    expect(acceptSequencedEvent(5, 3)).toEqual({ accepted: false, nextCursor: 5, reason: 'duplicate' });
  });

  it('holds an out-of-order event so reconnect replay can request the missing sequence', () => {
    expect(acceptSequencedEvent(5, 7)).toEqual({ accepted: false, nextCursor: 5, reason: 'gap' });
  });

  it('allows legitimate gaps for role-filtered organization streams', () => {
    expect(acceptSequencedEvent(5, 7, false)).toEqual({ accepted: true, nextCursor: 7, reason: 'accepted' });
  });
});
