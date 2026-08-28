import { screen } from '@testing-library/react';

import { renderApp } from '../test/render';
import { TodayPage } from './TodayPage';

describe('TodayPage', () => {
  it('provides a useful, accessible disconnected state without exposing a token', () => {
    renderApp(<TodayPage />);
    expect(screen.getByRole('heading', { name: /build the week/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /synthetic organization is ready/i })).toBeInTheDocument();
    expect(screen.getByText('ORG-DEMO-FIDOS-001')).toBeInTheDocument();
    expect(screen.queryByText(/bearer/i)).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Program pulse' })).toBeInTheDocument();
  });
});
