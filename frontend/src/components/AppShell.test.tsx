import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { App } from '../App';
import { renderApp } from '../test/render';

describe('AppShell', () => {
  it('uses a distinct route for every primary menu workspace', () => {
    renderApp(<App />);
    const navigation = screen.getByRole('navigation', { name: 'Primary workspaces' });
    const expected = new Map([
      ['Today', '/'],
      ['Playbook', '/playbook'],
      ['Film Room', '/film'],
      ['Practice', '/practice'],
      ['Scouting', '/scouting'],
      ['Game Plan', '/game-plan'],
    ]);

    for (const [name, path] of expected) {
      expect(within(navigation).getByRole('link', { name })).toHaveAttribute('href', path);
    }
    expect(new Set(expected.values()).size).toBe(expected.size);
    expect(screen.getByRole('link', { name: /pending reviews/i })).toHaveAttribute('href', '/inbox');
    expect(document.querySelector('[href*="operator-dashboard#"]')).not.toBeInTheDocument();
  });

  it('opens command search with the keyboard shortcut and exposes labeled destinations', async () => {
    const user = userEvent.setup();
    renderApp(<App />);
    await user.keyboard('{Control>}k{/Control}');
    const dialog = screen.getByRole('dialog', { name: 'Command search' });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByLabelText('Search navigation and plays')).toHaveFocus();
    expect(within(dialog).getByRole('link', { name: 'Playbook' })).toHaveAttribute('href', '/playbook');
  });
});
