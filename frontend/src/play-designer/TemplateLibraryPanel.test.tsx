import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import type { PlayDesign, PlayTemplate } from '../types';
import { TemplateLibraryPanel } from './TemplateLibraryPanel';

const DESIGN: PlayDesign = {
  id: 'PD-TEMPLATE-TEST', unit: 'offense', formation: 'shotgun_2x2', personnel: '11', _revision: 2,
  players: [{ id: 'X', alignment_key: 'X', position: 'WR', start: { x: 10, y: 32 } }],
  elements: [{ id: 'E-1', kind: 'route', type: 'post', points: [{ x: 10, y: 32 }, { x: 25, y: 10 }] }],
};

const TEMPLATE: PlayTemplate = {
  id: 'TPL-TEST', name: 'Dagger package', unit: 'offense', formation: 'shotgun_2x2', template_kind: 'concept_layer', layer: 'route_concept', version: '1.0.0', status: 'approved', scope: 'system',
  description: 'Clear and dig the middle.', tags: ['third-down'], assignments: [{ key: 'X-GO', slot: 'X', kind: 'route', type: 'go', points: [{ dx: 0, dy: 0 }, { dx: 0, dy: -20 }] }],
};

describe('TemplateLibraryPanel', () => {
  it('filters packages and requires confirmation before replacing existing work', async () => {
    const user = userEvent.setup();
    const onApply = vi.fn();
    render(<TemplateLibraryPanel templates={[TEMPLATE]} design={DESIGN} onApply={onApply} />);

    expect(screen.getByText('Dagger package')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Use package' }));
    expect(screen.getByRole('alert')).toHaveTextContent('replaces the current 1 assignments');
    expect(onApply).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Confirm replace' }));
    expect(onApply).toHaveBeenCalledWith(TEMPLATE, 'replace');
  });

  it('captures a saved call with a source description and tags', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<TemplateLibraryPanel templates={[]} design={DESIGN} onApply={vi.fn()} onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: 'Save current play as template' }));
    await user.type(screen.getByLabelText('Template name'), 'Boundary package');
    await user.type(screen.getByLabelText('Description'), 'Use on third down.');
    await user.type(screen.getByLabelText('Tags'), 'third-down, boundary');
    await user.click(screen.getByRole('button', { name: 'Capture template' }));
    expect(onSave).toHaveBeenCalledWith({ name: 'Boundary package', description: 'Use on third down.', tags: ['third-down', 'boundary'] });
  });
});
