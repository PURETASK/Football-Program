import { render, screen } from '@testing-library/react';

import type { PlayDesign } from '../types';
import { FieldThumbnail } from './FieldThumbnail';

const DESIGN: PlayDesign = {
  id: 'PD-TEST-DAGGER',
  name: 'Dagger',
  unit: 'offense',
  personnel: '11',
  formation: 'trips_right',
  players: [{ id: 'WR-X', position: 'WR', start: { x: 15, y: 24 } }],
  elements: [{ id: 'ROUTE-X', kind: 'route', player_id: 'WR-X', points: [{ x: 15, y: 24 }, { x: 32, y: 14 }, { x: 48, y: 14 }] }],
};

describe('FieldThumbnail', () => {
  it('renders an accessible football diagram from canonical player and route geometry', () => {
    render(<FieldThumbnail design={DESIGN} name="Dagger" />);
    expect(screen.getByRole('img', { name: 'Dagger offense field diagram' })).toBeInTheDocument();
    expect(document.querySelectorAll('path[marker-end]').length).toBe(1);
    expect(document.querySelectorAll('circle').length).toBe(1);
  });
});
