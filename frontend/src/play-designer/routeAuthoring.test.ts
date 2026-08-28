import { describe, expect, it } from 'vitest';
import { routeAuthoringPatch } from './routeAuthoring';

describe('route construction authoring', () => {
  it('stores stem, break, finish, and option semantics in the route phase', () => {
    expect(routeAuthoringPatch({ route_family: 'dropback', stem_depth_yards: 12, break_type: 'dig', break_depth_yards: 12, finish_direction: 'inside', option_rule: 'leverage' })).toMatchObject({ route_family: 'dropback', stem_depth_yards: 12, break_type: 'dig', break_depth_yards: 12, finish_direction: 'inside', option_rule: 'leverage', phase: 'route' });
  });
});
