import { describe, expect, it } from 'vitest';

import { filmLinkPath, parseFilmLinkedRecordRefs } from './filmLinks';

describe('film evidence links', () => {
  it('parses only governed downstream workspace references', () => {
    expect(parseFilmLinkedRecordRefs('scouting:SCOUT-1, game_plan:GAMEPLAN-1, invalid:X-1, player_development:ASSIGNMENT-1')).toEqual([
      { record_type: 'scouting', record_id: 'SCOUT-1', label: 'SCOUT-1' },
      { record_type: 'game_plan', record_id: 'GAMEPLAN-1', label: 'GAMEPLAN-1' },
      { record_type: 'player_development', record_id: 'ASSIGNMENT-1', label: 'ASSIGNMENT-1' },
    ]);
  });

  it('creates safe workspace navigation with a record query', () => {
    expect(filmLinkPath({ record_type: 'game_plan', record_id: 'GAMEPLAN-1' })).toBe('/app/game-plan?record=GAMEPLAN-1&record_type=game_plan');
  });
});
