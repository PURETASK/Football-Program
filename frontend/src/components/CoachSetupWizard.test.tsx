import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { renderApp } from '../test/render';
import { App } from '../App';

describe('CoachSetupWizard', () => {
  it('walks a head coach through a saved setup draft without pretending to create it while disconnected', async () => {
    const user = userEvent.setup();
    window.localStorage.clear();
    renderApp(<App />);
    await user.click(screen.getByRole('button', { name: 'Coach setup' }));
    expect(screen.getByRole('dialog', { name: 'Build your program context' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Continue/ }));
    await user.click(screen.getByRole('button', { name: /Continue/ }));
    await user.click(screen.getByRole('button', { name: /Continue/ }));
    await user.click(screen.getByRole('button', { name: /Create draft context/ }));
    expect(screen.getByRole('alert')).toHaveTextContent(/Connect an owner organization session/);
    expect(window.localStorage.getItem('nfl-fidos-coach-setup-draft-v1')).toContain('Demo Football Program');
  });
});
