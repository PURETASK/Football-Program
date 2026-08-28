import { describe, expect, it } from 'vitest';

import { FILM_FRAME_RATE, filmFrameStep } from './FilmStudioPanel';

describe('Film Studio transport helpers', () => {
  it('uses the declared frame rate for deterministic frame stepping', () => {
    expect(FILM_FRAME_RATE).toBe(30);
    expect(filmFrameStep(3, -1)).toBeCloseTo(3 - 1 / 30);
    expect(filmFrameStep(3, 1)).toBeCloseTo(3 + 1 / 30);
  });

  it('never seeks before the beginning of the asset', () => {
    expect(filmFrameStep(0, -1)).toBe(0);
  });
});
