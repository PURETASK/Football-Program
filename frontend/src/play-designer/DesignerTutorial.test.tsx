import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import { DESIGNER_TUTORIAL_STEPS, DesignerTutorial } from './DesignerTutorial';

describe('DesignerTutorial', () => {
  it('explains the designer and advances through the guided steps', async () => {
    const user = userEvent.setup();
    const onStep = vi.fn();
    const onComplete = vi.fn();
    const view = render(<DesignerTutorial open stepIndex={0} onStep={onStep} onClose={vi.fn()} onComplete={onComplete} />);

    expect(screen.getByRole('dialog', { name: 'Build one canonical football call' })).toBeVisible();
    expect(screen.getByText('The organization-scoped Python API remains canonical.')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Next' }));
    expect(onStep).toHaveBeenCalledWith(1);

    view.rerender(<DesignerTutorial open stepIndex={DESIGNER_TUTORIAL_STEPS.length - 1} onStep={onStep} onClose={vi.fn()} onComplete={onComplete} />);
    await user.click(screen.getByRole('button', { name: 'Finish tutorial' }));
    expect(onComplete).toHaveBeenCalledOnce();
  });

  it('can be dismissed with Escape without changing the play', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<DesignerTutorial open stepIndex={2} onStep={vi.fn()} onClose={onClose} onComplete={vi.fn()} />);

    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledOnce();
  });
});
