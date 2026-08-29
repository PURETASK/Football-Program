import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import type { PlayAsset, PlayDesign, PlayTemplate } from '../types';
import { PositionToolkit } from './PositionToolkit';

const design: PlayDesign = { id: 'TOOLKIT-1', unit: 'offense', formation: 'shotgun_2x2', players: [], elements: [] };
const assets: PlayAsset[] = [
  { id: 'POST', category: 'route', kind: 'route', term: 'post', display_name: 'Post', unit: 'offense', status: 'active', default_timing_ms: 1500, description: 'Break inside after the vertical stem.' },
  { id: 'JET', category: 'motion', kind: 'motion', term: 'jet', display_name: 'Jet Motion', unit: 'offense', status: 'active' },
];
const templates: PlayTemplate[] = [{ id: 'DAGGER', name: 'Dagger', unit: 'offense', layer: 'route_concept', scope: 'system' }];

describe('PositionToolkit', () => {
  it('exposes recommended actions and layers them through the parent editor callbacks', () => {
    const onChooseAsset = vi.fn();
    const onApplyTemplate = vi.fn();
    const onMaterializeAsset = vi.fn();
    render(<PositionToolkit player={{ id: 'X', position: 'WR', start: { x: 12, y: 26 } }} design={design} assets={assets} templates={templates} onChooseAsset={onChooseAsset} onApplyTemplate={onApplyTemplate} onMaterializeAsset={onMaterializeAsset} />);

    expect(screen.getByRole('heading', { name: 'WR options' })).toBeInTheDocument();
    expect(screen.getByText('Break inside after the vertical stem. Compatible with the current play context.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Draw Post from WR' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Draw Post from WR' }));
    expect(onChooseAsset).toHaveBeenCalledWith(assets[0]);
    fireEvent.click(screen.getByRole('button', { name: /Add Post starting action/ }));
    expect(onMaterializeAsset).toHaveBeenCalledWith(assets[0]);

    fireEvent.click(screen.getByRole('button', { name: /Dagger/ }));
    expect(onApplyTemplate).toHaveBeenCalledWith(templates[0], 'layer');
  });

  it('prefers authoritative server ranking and explains the recommendation', () => {
    const onChooseAsset = vi.fn();
    const serverAsset: PlayAsset = { id: 'SERVER-RUN', category: 'run', kind: 'run', term: 'inside_zone', display_name: 'Inside Zone', unit: 'offense', recommendation: { family: 'eligible', score: 97, reason: 'Catalog recommendation for this position' } };
    const serverTemplate: PlayTemplate = { id: 'SERVER-TEMPLATE', name: 'Server Concept', unit: 'offense', layer: 'route_concept', recommendation: { family: 'eligible', score: 91, reason: 'Template layer matches the position toolkit' } };
    render(<PositionToolkit player={{ id: 'X', position: 'WR', start: { x: 12, y: 26 } }} design={design} assets={assets} templates={templates} positionOptions={{ position: 'WR', unit: 'offense', family: 'eligible', status: 'ready', assets: [serverAsset], templates: [serverTemplate] }} onChooseAsset={onChooseAsset} onApplyTemplate={vi.fn()} />);

    expect(screen.getByText((content) => content.includes('Ranked for this play context by the team catalog.'))).toBeInTheDocument();
    expect(screen.getByText('Inside Zone')).toBeInTheDocument();
    expect(screen.queryByText('Post')).not.toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('Template layer matches the position toolkit'))).toBeInTheDocument();
  });
});
