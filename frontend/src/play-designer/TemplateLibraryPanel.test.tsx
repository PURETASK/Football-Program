import { fireEvent, render, screen } from '@testing-library/react';
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

  it('captures only selected assignments as a reusable stencil', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<TemplateLibraryPanel templates={[]} design={DESIGN} selectedElementIds={['E-1']} onApply={vi.fn()} onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: 'Save current play as template' }));
    await user.type(screen.getByLabelText('Template name'), 'Clear-out stencil');
    await user.click(screen.getByRole('checkbox', { name: /Capture only the 1 selected assignment/ }));
    await user.click(screen.getByRole('button', { name: 'Capture selected stencil' }));
    expect(onSave).toHaveBeenCalledWith({ name: 'Clear-out stencil', description: '', tags: [], elementIds: ['E-1'] });
  });

  it('shows inherited package lineage and sends the selected parent', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    const parent = { ...TEMPLATE, id: 'TPL-PARENT', name: 'Base route family' };
    render(<TemplateLibraryPanel templates={[parent]} design={DESIGN} onApply={vi.fn()} onSave={onSave} />);

    expect(screen.getByText('Base route family')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Save current play as template' }));
    await user.type(screen.getByLabelText('Template name'), 'Boundary variation');
    await user.selectOptions(screen.getByRole('combobox', { name: 'Inherit from existing package' }), 'TPL-PARENT');
    await user.click(screen.getByRole('button', { name: 'Capture template' }));
    expect(onSave).toHaveBeenCalledWith({ name: 'Boundary variation', description: '', tags: [], parentTemplateId: 'TPL-PARENT' });
  });

  it('expands field-level changes for a generated variant', async () => {
    const user = userEvent.setup();
    const variant: PlayDesign = { ...DESIGN, id: 'PD-VARIANT', coverage: 'cover_3', elements: [{ ...DESIGN.elements![0], type: 'corner' }, { id: 'E-2', kind: 'route', type: 'flat', points: [{ x: 20, y: 32 }, { x: 30, y: 28 }] }] };
    const onCreateVariants = vi.fn().mockResolvedValue({ variants: [variant], count: 1 });
    render(<TemplateLibraryPanel templates={[]} design={DESIGN} onApply={vi.fn()} onCreateVariants={onCreateVariants} onOpenVariant={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Optional assignment transformations'), { target: { value: '[{"element_id":"E-1","patch":{"type":"corner"}}]' } });
    await user.click(screen.getByRole('button', { name: 'Generate draft variants' }));
    expect(onCreateVariants).toHaveBeenCalledWith({ field: 'coverage', labels: ['Cover 3', 'Cover 1', 'Quarters'], assignmentPatches: [{ element_id: 'E-1', patch: { type: 'corner' } }] });
    expect(screen.getByText(/1 metadata · 1 assignment changes/)).toBeVisible();
    await user.click(screen.getByText('Inspect field-level changes'));
    expect(screen.getAllByText('Coverage').at(-1)).toBeVisible();
    expect(screen.getByText('E-1')).toBeVisible();
    expect(screen.getByText('Type: post → corner')).toBeVisible();
    expect(screen.getByText('E-2')).toBeVisible();
  });
});
