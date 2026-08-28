import type { PlayAsset, PlayDesign, PlayPlayer, PlayTemplate } from '../types';
import { positionAssetOptions, positionProfile, positionTemplateOptions } from './positionOptions';

const OFFENSE: PlayDesign = { id: 'OFF-1', unit: 'offense', formation: 'shotgun_2x2', players: [], elements: [] };
const DEFENSE: PlayDesign = { id: 'DEF-1', unit: 'defense', front: '4-2-5_over', players: [], elements: [] };

function asset(id: string, category: string, unit: string = 'offense'): PlayAsset {
  return { id, category, kind: category, term: id.toLowerCase(), unit, status: 'active' };
}

describe('position-aware play authoring options', () => {
  it('ranks eligible receiver routes ahead of structural alignment assets', () => {
    const player: PlayPlayer = { id: 'X', position: 'WR', start: { x: 12, y: 26 } };
    const options = positionAssetOptions(player, OFFENSE, [
      asset('FORMATION', 'formation'),
      asset('FRONT', 'front'),
      asset('POST', 'route'),
      asset('JET', 'motion'),
    ]);

    expect(positionProfile(player, 'offense').family).toBe('eligible');
    expect(options.map((item) => item.id)).toEqual(['POST', 'JET']);
  });

  it('prioritizes linebacker fit and pressure actions from the defensive registry', () => {
    const player: PlayPlayer = { id: 'MIKE', position: 'MLB', start: { x: 50, y: 18 } };
    const options = positionAssetOptions(player, DEFENSE, [
      asset('COVER-3', 'coverage', 'defense'),
      asset('FIT-A', 'fit', 'defense'),
      asset('BLITZ-A', 'rush', 'defense'),
      asset('DIG', 'route'),
    ]);

    expect(positionProfile(player, 'defense').family).toBe('linebacker');
    expect(options[0].id).toBe('FIT-A');
    expect(options.findIndex((item) => item.id === 'BLITZ-A')).toBeLessThan(options.findIndex((item) => item.id === 'DIG'));
    expect(options.at(-1)?.id).toBe('DIG');
  });

  it('suggests reusable layers that match the selected unit and role family', () => {
    const player: PlayPlayer = { id: 'Y', position: 'TE', start: { x: 68, y: 26 } };
    const templates: PlayTemplate[] = [
      { id: 'ROUTE', name: 'Flood', unit: 'offense', layer: 'route_concept' },
      { id: 'PROTECTION', name: 'Half slide', unit: 'offense', layer: 'protection' },
      { id: 'COVERAGE', name: 'Cover 3', unit: 'defense', layer: 'coverage_layer' },
    ];

    expect(positionTemplateOptions(player, OFFENSE, templates).map((item) => item.id)).toEqual(['ROUTE', 'PROTECTION']);
  });
});
