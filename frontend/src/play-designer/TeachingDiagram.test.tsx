import { render, screen } from '@testing-library/react';

import type { PlayRoleView } from '../types';
import { TeachingDiagram } from './TeachingDiagram';

const VIEW: PlayRoleView = {
  id: 'VIEW-1',
  play_id: 'PLAY-1',
  role: 'WR',
  mode: 'player',
  players: [{ id: 'WR-1', position: 'WR', start: { x: 10, y: 30 } }],
  context_players: [],
  elements: [{ id: 'ROUTE-1', kind: 'route', type: 'post', player_id: 'WR-1', points: [{ x: 10, y: 30 }, { x: 35, y: 10 }] }],
  steps: [{ id: 'STEP-1', element_id: 'ROUTE-1', label: 'WR · post', instruction: 'Stem vertical then break.', start_ms: 0, end_ms: 1200, step_index: 0, revealed: true }],
  read_reveal: [],
  quizzes: [],
  mastery: { design_id: 'PLAY-1', attempts: [], summary: {} },
};

describe('TeachingDiagram', () => {
  it('renders the filtered role diagram and accessible playback controls', () => {
    render(<TeachingDiagram view={VIEW} stepIndex={0} onStepChange={() => undefined} />);
    expect(screen.getByRole('region', { name: 'Filtered teaching diagram' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'WR filtered football diagram with 1 assignments' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Play active assignment' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Step reveal' })).toHaveValue('0');
  });

  it('shows synchronized before/after exchange context for defensive teaching', () => {
    const view: PlayRoleView = { ...VIEW, role: 'WLB', mode: 'player', players: [{ id: 'DE-1', position: 'DE', start: { x: 36, y: 20 } }, { id: 'LB-1', position: 'WLB', start: { x: 48, y: 20 } }], elements: [
      { id: 'RUSH-1', kind: 'rush', player_id: 'DE-1', exchange_with: 'DROP-1', exchange_role: 'penetrate_loop', points: [{ x: 36, y: 20 }, { x: 42, y: 28 }] },
      { id: 'DROP-1', kind: 'coverage', player_id: 'LB-1', exchange_with: 'RUSH-1', exchange_role: 'loop_penetrate', replacement_zone: 'flat_left', points: [{ x: 48, y: 20 }, { x: 46, y: 29 }] },
    ], steps: [{ id: 'STEP-EX', element_id: 'DROP-1', label: 'WLB · replace', instruction: 'Replace the flat.', exchange_with: 'RUSH-1', exchange_role: 'drop_replace', gap_owner: 'left_b', replacement_zone: 'flat_left', start_ms: 250, end_ms: 850, step_index: 0, revealed: true }] };
    render(<TeachingDiagram view={view} stepIndex={0} onStepChange={() => undefined} />);
    expect(screen.getByRole('status')).toHaveTextContent('After exchange');
    expect(screen.getByRole('group', { name: 'After exchange between DROP-1 and RUSH-1' })).toBeInTheDocument();
    expect(screen.getByText('Replaces flat_left')).toBeInTheDocument();
  });
});
