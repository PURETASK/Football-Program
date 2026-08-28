import type { PlayDesign } from '../types';
import { remoteRevisionDecision } from './remoteRevision';

const DESIGN: PlayDesign = { id: 'PLAY-REMOTE', name: 'Remote', unit: 'offense', _revision: 4 };

describe('remote revision handoff', () => {
  it('applies a newer server revision when the editor is clean', () => {
    expect(remoteRevisionDecision({ present: DESIGN, dirty: false, serverRevision: 4 }, { ...DESIGN, _revision: 5 })).toBe('apply');
  });

  it('preserves local work behind an explicit conflict when dirty', () => {
    expect(remoteRevisionDecision({ present: DESIGN, dirty: true, serverRevision: 4 }, { ...DESIGN, _revision: 5 })).toBe('conflict');
  });

  it('ignores stale or unrelated revisions', () => {
    expect(remoteRevisionDecision({ present: DESIGN, dirty: false, serverRevision: 4 }, { ...DESIGN, _revision: 4 })).toBe('ignore');
    expect(remoteRevisionDecision({ present: DESIGN, dirty: false, serverRevision: 4 }, { ...DESIGN, id: 'OTHER', _revision: 8 })).toBe('ignore');
  });
});
