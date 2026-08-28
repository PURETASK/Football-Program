import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import { renderApp } from '../test/render';
import { SessionDialog } from './SessionDialog';

describe('SessionDialog', () => {
  it('closes with Escape for keyboard users', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderApp(<SessionDialog open onClose={onClose} />);
    expect(screen.getByRole('dialog', { name: 'Connect your organization' })).toBeInTheDocument();
    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('keeps keyboard focus inside the dialog', async () => {
    const user = userEvent.setup();
    renderApp(<SessionDialog open onClose={() => undefined} />);
    await waitFor(() => expect(screen.getByLabelText('Organization ID')).toHaveFocus());
    const closeButton = screen.getByRole('button', { name: 'Close team access dialog' });
    closeButton.focus();
    await user.tab({ shift: true });
    expect(screen.getByRole('button', { name: 'Connect securely' })).toHaveFocus();
  });

  it('explains malformed credentials instead of storing them', async () => {
    const user = userEvent.setup();
    renderApp(<SessionDialog open onClose={() => undefined} />);
    await user.type(screen.getByLabelText('Bearer token'), 'not-a-token');
    await user.click(screen.getByRole('button', { name: 'Connect securely' }));
    expect(screen.getByRole('alert')).toHaveTextContent('token format');
    expect(sessionStorage.length).toBe(0);
  });
});
