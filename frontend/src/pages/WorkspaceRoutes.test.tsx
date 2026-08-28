import { screen, within } from '@testing-library/react';

import { App } from '../App';
import { renderApp } from '../test/render';

const ROUTES = [
  ['/inbox', 'Operations Inbox'],
  ['/roster', 'Roster & Personnel'],
  ['/analytics', 'Outcome Analytics'],
  ['/delivery', 'Delivery Center'],
  ['/collaboration', 'Staff Collaboration'],
  ['/film', 'Film Room'],
  ['/practice', 'Practice'],
  ['/scouting', 'Scouting'],
  ['/game-plan', 'Game Plan'],
  ['/player', 'Player Development'],
  ['/admin', 'Admin & Governance'],
  ['/reviews', 'Reviews & Approvals'],
] as const;

describe('individual workspace routes', () => {
  it.each(ROUTES)('renders %s as its own described page', async (path, title) => {
    renderApp(<App />, { initialEntries: [path] });

    expect(await screen.findByRole('heading', { name: title, level: 1 })).toBeVisible();
    expect(screen.getByText('About this page.', { exact: false })).toBeVisible();
    expect(screen.getByRole('heading', { name: `${title} system` })).toBeVisible();
    const features = screen.getByRole('region', { name: `${title} features` });
    expect(within(features).getAllByText('How it operates')).toHaveLength(4);
    expect(screen.getByRole('region', { name: `${title} operating workflow` })).toBeVisible();
    expect(screen.getByRole('region', { name: 'What this system will not do silently' })).toBeVisible();
    expect(screen.queryByRole('link', { name: /Open current workflow/i })).not.toBeInTheDocument();
  });

  it('renders Stage 25 acceptance as a dedicated governance route', async () => {
    renderApp(<App />, { initialEntries: ['/admin/stage-25'] });

    expect(await screen.findByRole('heading', { name: 'Stage 25 specification acceptance', level: 1 })).toBeVisible();
    expect(screen.getByText('About this page.', { exact: false })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Specification acceptance system' })).toBeVisible();
  });

  it('renders organization population readiness as a dedicated governance route', async () => {
    renderApp(<App />, { initialEntries: ['/admin/population-readiness'] });

    expect(await screen.findByRole('heading', { name: 'Organization population readiness', level: 1 })).toBeVisible();
    expect(screen.getByText('About this page.', { exact: false })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Population readiness system' })).toBeVisible();
  });
});
