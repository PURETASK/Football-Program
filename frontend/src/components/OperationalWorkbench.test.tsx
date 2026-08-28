import { Database, Film } from 'lucide-react';
import { fireEvent, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { renderApp } from '../test/render';
import { RecordList, WorkbenchFrame, WorkbenchState, WorkbenchTabs } from './OperationalWorkbench';

describe('operational workbench primitives', () => {
  it('provides keyboard-reachable tabs and selected-record state', () => {
    const change = vi.fn();
    const select = vi.fn();
    renderApp(
      <WorkbenchFrame description="Film operations" eyebrow="Live" icon={Film} title="Film workbench">
        <WorkbenchTabs activeTab="clips" label="Film views" onChange={change} tabs={[{ id: 'clips', label: 'Clips', count: 2 }, { id: 'tags', label: 'Tags', count: 1 }]} />
        <RecordList onSelect={select} records={[{ id: 'CLIP-1', status: 'ready' }]} selectedId="CLIP-1" title={(record) => record.id} />
      </WorkbenchFrame>,
    );

    const tags = screen.getByRole('tab', { name: /Tags/ });
    fireEvent.click(tags);
    expect(change).toHaveBeenCalledWith('tags');
    const clip = screen.getByRole('listitem');
    expect(clip).toHaveAttribute('aria-current', 'true');
    fireEvent.click(clip);
    expect(select).toHaveBeenCalledWith({ id: 'CLIP-1', status: 'ready' });
  });

  it('explains the disconnected control state without rendering active mutations', () => {
    renderApp(<WorkbenchState connected={false} loading={false}><Database data-testid="active-control" /></WorkbenchState>);
    expect(screen.getByRole('status')).toHaveTextContent('Connect an organization session');
    expect(screen.queryByTestId('active-control')).not.toBeInTheDocument();
  });
});
