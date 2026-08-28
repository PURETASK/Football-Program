import type { PlayAsset, PlayDesign } from '../types';
import { materializeAssetAction } from './actionMaterializer';

const offense: PlayDesign = {
  id: 'MAT-OFF',
  unit: 'offense',
  field_context: { direction: 'right' },
  players: [],
  elements: [],
};

const defense: PlayDesign = {
  id: 'MAT-DEF',
  unit: 'defense',
  field_context: { direction: 'left' },
  players: [],
  elements: [],
};

describe('player action materializer', () => {
  it('creates an editable route with registry linkage, depth, timing, and teaching metadata', () => {
    const asset: PlayAsset = { id: 'ROUTE-POST', category: 'route', kind: 'route', term: 'post', unit: 'offense', default_timing_ms: 1500, arrow_style: 'route', description: 'Break inside.', accessibility: 'Vertical stem and inside break.' };
    const element = materializeAssetAction(offense, { id: 'X', position: 'WR', start: { x: 12, y: 32 } }, asset);

    expect(element).toMatchObject({ kind: 'route', player_id: 'X', asset_id: 'ROUTE-POST', type: 'post', start_ms: 0, end_ms: 1500, depth_yards: 12, landmark: 'Vertical stem then break', phase: 'post_snap', line_style: 'solid', arrow_ends: 'end', path_mode: 'smooth' });
    expect(element.points?.[0]).toEqual({ x: 12, y: 32 });
    expect(element.points?.length).toBeGreaterThan(2);
    expect(element.timing?.phases?.length).toBeGreaterThan(0);
  });

  it('creates pre-snap motion and defensive pressure paths in the correct semantic direction', () => {
    const motion: PlayAsset = { id: 'MOTION-JET', category: 'motion', kind: 'motion', term: 'jet', unit: 'offense', default_timing_ms: 450, arrow_style: 'motion' };
    const rush: PlayAsset = { id: 'RUSH-EDGE', category: 'rush', kind: 'rush', term: 'edge', unit: 'defense', arrow_style: 'rush' };
    const motionElement = materializeAssetAction(offense, { id: 'Z', position: 'WR', start: { x: 80, y: 32 } }, motion);
    const rushElement = materializeAssetAction(defense, { id: 'EDGE', position: 'DE', start: { x: 70, y: 20 } }, rush);

    expect(motionElement).toMatchObject({ start_ms: -450, end_ms: 0, phase: 'pre_snap', line_style: 'dashed' });
    expect(motionElement.points?.at(-1)?.x).toBeGreaterThan(80);
    expect(rushElement).toMatchObject({ kind: 'rush', phase: 'post_snap', landmark: 'Rush landmark through assigned gap' });
    expect(rushElement.points?.at(-1)?.y).toBeGreaterThan(20);
  });
});
