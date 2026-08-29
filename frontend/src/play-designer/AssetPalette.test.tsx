import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import type { PlayAsset, PlayDesign } from '../types';
import { AssetPalette } from './AssetPalette';

const DESIGN: PlayDesign = { id: 'PD-ASSET-TEST', unit: 'offense', formation: 'shotgun_trips', personnel: '11', rule_profile: 'nfl' };
const ASSETS: PlayAsset[] = [
  {
    id: 'ASSET-POST', kind: 'route', category: 'route', term: 'post', display_name: 'Post', unit: 'offense', aliases: ['skinny post'], status: 'active', description: 'Break inside at depth.',
    compatibility: { compatible: true, selectable: true, score: 100, reasons: [], warnings: [], basis: ['formation:shotgun_trips'] },
  },
  {
    id: 'ASSET-ANGLE', kind: 'route', category: 'route', term: 'angle', display_name: 'Angle', unit: 'offense', aliases: ['Texas'], status: 'active', description: 'Back breaks inside.',
    compatibility: { compatible: false, selectable: true, score: 70, reasons: ['Not cataloged for formation shotgun trips.'], warnings: [], basis: ['formation:shotgun_trips'] },
  },
  {
    id: 'ASSET-OLD', kind: 'route', category: 'route', term: 'old_route', display_name: 'Old Route', unit: 'offense', status: 'deprecated', replacement_id: 'ASSET-POST',
    compatibility: { compatible: false, selectable: false, score: 20, reasons: ['Asset lifecycle state is deprecated.'], warnings: ['Use replacement ASSET-POST for new authoring.'], basis: [], replacement_id: 'ASSET-POST' },
  },
];

describe('AssetPalette', () => {
  it('uses server compatibility, lifecycle filters, aliases, and disabled replacements', () => {
    const onChoose = vi.fn();
    render(<AssetPalette assets={ASSETS} design={DESIGN} activeAsset={null} onChoose={onChoose} />);
    expect(screen.getByTitle('2 matching of 3 assets')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Post diagram preview' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Fits call/i }));
    expect(screen.getByRole('button', { name: /Post/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Angle/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Fits call/i }));
    fireEvent.change(screen.getByLabelText('Search play assets'), { target: { value: 'Texas' } });
    expect(screen.getByRole('button', { name: /Angle/i })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Asset lifecycle'), { target: { value: 'all' } });
    fireEvent.change(screen.getByLabelText('Search play assets'), { target: { value: 'Old Route' } });
    expect(screen.getByRole('button', { name: /Old Route/i })).toBeDisabled();
  });
});
