import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import type { PlayAsset, PlayDesign, PlayTemplate } from '../types';
import { PositionToolkit } from './PositionToolkit';

const design: PlayDesign = { id: 'TOOLKIT-1', unit: 'offense', formation: 'shotgun_2x2', players: [], elements: [] };
const assets: PlayAsset[] = [
  { id: 'POST', category: 'route', kind: 'route', term: 'post', display_name: 'Post', unit: 'offense', status: 'active', default_timing_ms: 1500 },
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
    expect(screen.getByRole('button', { name: 'Draw Post from WR' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Draw Post from WR' }));
    expect(onChooseAsset).toHaveBeenCalledWith(assets[0]);
    fireEvent.click(screen.getByRole('button', { name: /Add Post starting action/ }));
    expect(onMaterializeAsset).toHaveBeenCalledWith(assets[0]);

    fireEvent.click(screen.getByRole('button', { name: /Dagger/ }));
    expect(onApplyTemplate).toHaveBeenCalledWith(templates[0], 'layer');
  });
});
