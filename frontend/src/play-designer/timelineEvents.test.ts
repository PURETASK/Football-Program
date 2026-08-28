import { timelineEventEnd, timelineEventKind, timelineEventStart, normalizeTimelineEvent } from './timelineEvents';

describe('timeline event compatibility', () => {
  it('reads legacy type and at_ms fields', () => {
    const event = { type: 'qb_read', at_ms: 650 };
    expect(timelineEventKind(event)).toBe('qb_read');
    expect(timelineEventStart(event)).toBe(650);
    expect(timelineEventEnd(event, 2000)).toBe(2000);
  });

  it('normalizes legacy records while preserving provider metadata', () => {
    expect(normalizeTimelineEvent({ id: 'READ', type: 'qb_read', at_ms: 650, source: 'seed' }, 2000)).toEqual({
      id: 'READ', type: 'qb_read', at_ms: 650, source: 'seed', kind: 'qb_read', start_ms: 650, end_ms: 2000,
    });
  });
});
