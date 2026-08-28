import { render, screen } from '@testing-library/react';

import { DescriptionBox } from './DescriptionBox';

describe('DescriptionBox', () => {
  it('explains a system purpose, operation, audience, and output', () => {
    render(
      <DescriptionBox
        audience="Coaching staff"
        description="Organizes canonical football calls."
        howItWorks="Reads organization-scoped records."
        outcome="A validated play library."
        title="Playbook system"
      />,
    );

    expect(screen.getByRole('heading', { name: 'Playbook system' })).toBeVisible();
    expect(screen.getByText('Organizes canonical football calls.')).toBeVisible();
    expect(screen.getByText('Reads organization-scoped records.')).toBeVisible();
    expect(screen.getByText('Coaching staff')).toBeVisible();
    expect(screen.getByText('A validated play library.')).toBeVisible();
  });
});
