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
      ['Operations Inbox', '/inbox'],
      ['Roster & Personnel', '/roster'],
      ['Outcome Analytics', '/analytics'],
      ['Delivery Center', '/delivery'],
      ['Collaboration', '/collaboration'],
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

  it('exposes and closes the responsive navigation through the keyboard', async () => {
    const user = userEvent.setup();
    renderApp(<App />);
    const openButton = screen.getByRole('button', { name: 'Open navigation' });
    expect(openButton).toHaveAttribute('aria-controls', 'primary-navigation');
    expect(openButton).toHaveAttribute('aria-expanded', 'false');

    await user.click(openButton);
    expect(openButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getAllByRole('button', { name: 'Close navigation' })).toHaveLength(2);
    expect(screen.getByRole('complementary', { name: 'Primary navigation' })).toHaveClass('sidebar--open');

    await user.keyboard('{Escape}');
    expect(openButton).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByRole('complementary', { name: 'Primary navigation' })).not.toHaveClass('sidebar--open');
    expect(document.querySelector('.sidebar-scrim')).not.toBeInTheDocument();
  });

  it('lets a coach choose an operating lens without changing authorization', async () => {
    const user = userEvent.setup();
    renderApp(<App />);
    await user.click(screen.getByRole('button', { name: 'Operating lens: Head coach' }));
    expect(screen.getByRole('dialog', { name: 'Choose your operating lens' })).toBeInTheDocument();
    expect(screen.getByText(/does not grant permissions/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Offensive coordinator/i }));
    expect(screen.getByRole('button', { name: 'Operating lens: Offensive coordinator' })).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: 'Choose your operating lens' })).not.toBeInTheDocument();
  });
});
