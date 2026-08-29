import { describe, expect, it } from 'vitest';

import { clearDefensiveExchangePairPatch, defensiveExchangeLinks, defensiveExchangePairPatch, defensiveExchangePresetCompatibility, defensiveExchangePresetPatch, defensiveExchangeProgress, exchangeConceptPatch, exchangePatch, reciprocalExchangePatch } from './defensiveExchanges';
import type { PlayDesign } from '../types';

describe('defensive exchange relationships', () => {
  it('creates a canonical current-side exchange patch', () => {
    expect(exchangePatch('RUSH-2', 'penetrate_loop')).toEqual({ exchange_with: 'RUSH-2', target_element_id: 'RUSH-2', exchange_role: 'penetrate_loop', phase: 'exchange' });
  });

  it('creates the reciprocal role for the linked partner', () => {
    expect(reciprocalExchangePatch('RUSH-1', 'penetrate_loop')).toEqual(expect.objectContaining({ exchange_with: 'RUSH-1', target_element_id: 'RUSH-1', exchange_role: 'loop_penetrate', phase: 'exchange' }));
  });

  it('clears an exchange without leaving a stale role', () => {
    expect(exchangePatch('', 'penetrate_loop')).toEqual({ exchange_with: undefined, target_element_id: undefined, exchange_role: undefined, phase: undefined });
  });

  it('projects reciprocal exchanges into one deduplicated field link', () => {
    const design: PlayDesign = { id: 'EXCHANGE', unit: 'defense', elements: [
      { id: 'RUSH-1', kind: 'rush', player_id: 'DE', exchange_with: 'DROP-1', exchange_role: 'penetrate_loop', points: [{ x: 35, y: 20 }, { x: 42, y: 28 }] },
      { id: 'DROP-1', kind: 'coverage', player_id: 'LB', exchange_with: 'RUSH-1', exchange_role: 'loop_penetrate', points: [{ x: 48, y: 20 }, { x: 46, y: 29 }] },
    ] };
    expect(defensiveExchangeLinks(design)).toEqual([expect.objectContaining({ fromId: 'DROP-1', toId: 'RUSH-1', label: 'Loop → penetrate', from: { x: 46, y: 29 }, to: { x: 42, y: 28 } })]);
  });

  it('creates both sides of a selected exchange pair with reciprocal roles', () => {
    expect(defensiveExchangePairPatch('RUSH-1', 'DROP-1', 'rush_replace')).toEqual([
      ['RUSH-1', expect.objectContaining({ exchange_with: 'DROP-1', exchange_role: 'rush_replace', phase: 'exchange' })],
      ['DROP-1', expect.objectContaining({ exchange_with: 'RUSH-1', exchange_role: 'drop_replace', phase: 'exchange' })],
    ]);
  });

  it('explains named exchange partner compatibility before authoring', () => {
    expect(defensiveExchangePresetCompatibility('tex', { id: 'DT', position: 'DT' }, { id: 'DE', position: 'DE' })).toEqual({ compatible: true, reasons: [] });
    expect(defensiveExchangePresetCompatibility('cross_dog', { id: 'DT', position: 'DT' }, { id: 'WILL', position: 'WILL' }).compatible).toBe(false);
    expect(defensiveExchangePresetCompatibility('cross_dog', { id: 'MIKE', position: 'MIKE' }, { id: 'WILL', position: 'WILL' })).toEqual({ compatible: true, reasons: [] });
  });

  it('materializes named TEX and replacement patterns as reciprocal pair patches', () => {
    expect(defensiveExchangePresetPatch('tex', 'TACKLE', 'END')).toEqual([
      ['TACKLE', expect.objectContaining({ exchange_with: 'END', exchange_role: 'penetrate_loop' })],
      ['END', expect.objectContaining({ exchange_with: 'TACKLE', exchange_role: 'loop_penetrate' })],
    ]);
    expect(defensiveExchangePresetPatch('rush_replace', 'RUSH', 'DROP', { replacement_zone: 'flat_left' })[1][1]).toMatchObject({ rotation_to_zone: 'flat_left', responsibility: 'Replace flat_left' });
  });

  it('stores relationship-level concept, trigger, and communication metadata', () => {
    expect(exchangeConceptPatch('tex', { trigger: 'on_guard_away', communication: 'TEX alert, exchange through the hip' })).toEqual({
      exchange_concept: 'tex',
      exchange_concept_label: 'TEX · tackle-end exchange',
      exchange_trigger: 'on_guard_away',
      exchange_communication: 'TEX alert, exchange through the hip',
      phase: 'exchange',
    });
    expect(exchangeConceptPatch('')).toEqual({ exchange_concept: undefined, exchange_concept_label: undefined, exchange_trigger: undefined, exchange_communication: undefined, phase: undefined });
  });

  it('persists vacated and replacement responsibility context on the appropriate sides', () => {
    expect(defensiveExchangePairPatch('RUSH-1', 'DROP-1', 'rush_replace', { vacated_zone: 'left_b', replacement_zone: 'flat_left' })).toEqual([
      ['RUSH-1', expect.objectContaining({ responsibility: 'Vacate left_b' })],
      ['DROP-1', expect.objectContaining({ rotation_to_zone: 'flat_left', zone: 'flat_left', responsibility: 'Replace flat_left' })],
    ]);
  });

  it('projects a replacement-zone anchor for rush-to-replace teaching', () => {
    const design: PlayDesign = { id: 'REPLACE', unit: 'defense', elements: [
      { id: 'RUSH', kind: 'rush', exchange_with: 'DROP', exchange_role: 'rush_replace', points: [{ x: 40, y: 20 }, { x: 46, y: 30 }] },
      { id: 'DROP', kind: 'coverage', exchange_with: 'RUSH', exchange_role: 'drop_replace', zone: 'flat_right', rotation_to_zone: 'flat_right', points: [{ x: 60, y: 20 }, { x: 55, y: 28 }] },
    ] };
    expect(defensiveExchangeLinks(design)[0].replacement).toEqual({ x: 86, y: 22, label: 'flat_right' });
  });

  it('clears both reciprocal links without leaving exchange metadata behind', () => {
    expect(clearDefensiveExchangePairPatch('RUSH-1', 'DROP-1')).toEqual([
      ['RUSH-1', expect.objectContaining({ exchange_with: undefined, target_element_id: undefined, exchange_role: undefined, phase: undefined })],
      ['DROP-1', expect.objectContaining({ exchange_with: undefined, target_element_id: undefined, exchange_role: undefined, phase: undefined })],
    ]);
  });

  it('reveals an exchange link from its synchronized event timing', () => {
    const design: PlayDesign = { id: 'TIMED-EXCHANGE', unit: 'defense', elements: [
      { id: 'RUSH', kind: 'rush', exchange_with: 'DROP', points: [{ x: 40, y: 20 }, { x: 46, y: 30 }] },
      { id: 'DROP', kind: 'coverage', exchange_with: 'RUSH', points: [{ x: 60, y: 20 }, { x: 55, y: 28 }] },
    ], timeline: { duration_ms: 2000, events: [{ id: 'EX', type: 'exchange', element_id: 'RUSH', at_ms: 400, end_ms: 800 }] } };
    const link = defensiveExchangeLinks(design)[0];
    expect(defensiveExchangeProgress(design, link, 200, 2000)).toBe(0);
    expect(defensiveExchangeProgress(design, link, 600, 2000)).toBeCloseTo(0.5);
    expect(defensiveExchangeProgress(design, link, 900, 2000)).toBe(1);
  });

  it('reveals an exchange link from a block/rush exchange cue', () => {
    const design: PlayDesign = { id: 'TIMED-BLOCK-RUSH', unit: 'defense', elements: [
      { id: 'RUSH', kind: 'rush', exchange_with: 'DROP', points: [{ x: 40, y: 20 }, { x: 46, y: 30 }] },
      { id: 'DROP', kind: 'coverage', exchange_with: 'RUSH', points: [{ x: 60, y: 20 }, { x: 55, y: 28 }] },
    ], timeline: { duration_ms: 2000, events: [{ id: 'BR', kind: 'rush_exchange', element_id: 'RUSH', start_ms: 400, end_ms: 800 }] } };
    const link = defensiveExchangeLinks(design)[0];
    expect(defensiveExchangeProgress(design, link, 600, 2000)).toBeCloseTo(0.5);
  });
});
