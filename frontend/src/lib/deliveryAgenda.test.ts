import { describe, expect, it } from 'vitest';

import { buildDeliveryAgenda } from './deliveryAgenda';
import type { DeliveryTask } from '../types';

const task = (id: string, due_at: string | undefined, status = 'open'): DeliveryTask => ({ id, title: id, category: 'install', due_at, status });

describe('buildDeliveryAgenda', () => {
  it('groups tasks by deadline day, orders them, and preserves overdue counts', () => {
    const result = buildDeliveryAgenda([
      task('later', '2026-08-30T10:00:00Z'),
      task('earlier', '2026-08-29T09:00:00Z'),
      task('done', '2026-08-29T08:00:00Z', 'completed'),
      task('unscheduled', undefined),
    ], Date.parse('2026-08-29T12:00:00Z'));
    expect(result.map((group) => group.key)).toEqual(['2026-08-29', '2026-08-30', 'unscheduled']);
    expect(result[0].tasks.map((item) => item.id)).toEqual(['done', 'earlier']);
    expect(result[0].openCount).toBe(1);
    expect(result[0].overdueCount).toBe(1);
  });
});
