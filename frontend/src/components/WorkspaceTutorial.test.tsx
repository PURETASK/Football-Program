import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { renderApp } from '../test/render';
import { App } from '../App';
import { WORKSPACE_TUTORIALS, tutorialForPath } from './WorkspaceTutorial';

describe('workspace tutorials', () => {
  it('maps every primary workspace to a tutorial and keeps the dedicated designer tutorial separate', () => {
    expect(tutorialForPath('/')).toBe(WORKSPACE_TUTORIALS.today);
    expect(tutorialForPath('/playbook')).toBe(WORKSPACE_TUTORIALS.playbook);
    expect(tutorialForPath('/practice')).toBeDefined();
    expect(tutorialForPath('/film')).toBeDefined();
    expect(tutorialForPath('/admin/population-readiness')).toBe(WORKSPACE_TUTORIALS.admin);
    expect(tutorialForPath('/playbook/designer/new')).toBeUndefined();
    expect(Object.keys(WORKSPACE_TUTORIALS)).toEqual(expect.arrayContaining([
      'today', 'playbook', 'inbox', 'roster', 'analytics', 'delivery', 'collaboration',
      'film', 'practice', 'scouting', 'game-plan', 'player', 'admin', 'reviews',
    ]));
  });

  it('opens from the workspace shell and supports guided progression', async () => {
    const user = userEvent.setup();
    renderApp(<App />, { initialEntries: ['/playbook'] });

    await user.click(screen.getByRole('button', { name: 'Open Playbook library tutorial' }));
    expect(screen.getByRole('dialog', { name: 'Find the right call' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Find the right call' })).toBeInTheDocument();
    expect(screen.getByText('1 of 3')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Next/ }));
    expect(screen.getByRole('heading', { name: 'Start from a governed template' })).toBeInTheDocument();
    expect(screen.getByText('2 of 3')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Next/ }));
    await user.click(screen.getByRole('button', { name: /Finish/ }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
