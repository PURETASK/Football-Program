import { describe, expect, it } from 'vitest';

import { reviewRecordKey } from './ReviewsPage';

describe('Reviews queue identity', () => {
  it('keeps collection and record identity together for selection highlighting', () => {
    expect(reviewRecordKey({ collection: 'play_designs', id: 'PLAY-1' })).toBe('play_designs:PLAY-1');
    expect(reviewRecordKey({ collection: 'practice_plans', id: 'PLAY-1' })).not.toBe('play_designs:PLAY-1');
  });
});
