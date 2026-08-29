import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { DesignerToolbar } from './DesignerToolbar';

describe('DesignerToolbar', () => {
  it('keeps compact icon actions named for assistive technology', () => {
    const action = vi.fn();
    render(
      <MemoryRouter>
        <DesignerToolbar
          design={{ id: 'PD-A11Y', name: 'Dagger', unit: 'offense', status: 'draft' }}
          tool="select"
          dirty={false}
          snap
          canUndo={false}
          canRedo={false}
          selectionCount={0}
          saveState="saved"
          presence={[]}
          onTool={action}
          onSave={action}
          onUndo={action}
          onRedo={action}
          onDuplicate={action}
          onCopy={action}
          onPaste={action}
          onMirror={action}
          onGroup={action}
          onDelete={action}
          onToggleSnap={action}
          onRequestReview={action}
          onExport={action}
          onTeaching={action}
          onTutorial={action}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole('button', { name: 'Export play' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Open review panel' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Open Play Designer tutorial' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Open teaching view' })).toBeVisible();
    expect(screen.getByRole('link', { name: 'Back to Playbook' })).toBeVisible();
  });

  it('does not advertise paste as actionable before a selection is copied', () => {
    const action = vi.fn();
    render(
      <MemoryRouter>
        <DesignerToolbar
          design={{ id: 'PD-PASTE', name: 'Paste test', unit: 'offense', status: 'draft' }}
          tool="select"
          dirty={false}
          snap
          canUndo={false}
          canRedo={false}
          selectionCount={0}
          hasClipboard={false}
          saveState="saved"
          presence={[]}
          onTool={action}
          onSave={action}
          onUndo={action}
          onRedo={action}
          onDuplicate={action}
          onCopy={action}
          onPaste={action}
          onMirror={action}
          onGroup={action}
          onDelete={action}
          onToggleSnap={action}
          onRequestReview={action}
          onExport={action}
          onTeaching={action}
          onTutorial={action}
        />
      </MemoryRouter>,
    );
    expect(screen.getByRole('button', { name: 'Paste selection' })).toBeDisabled();
  });
});
