import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import type { PlayDesign } from '../types';
import { DesignerInspector } from './DesignerInspector';

const DESIGN: PlayDesign = {
  id: 'DESIGN-INSPECTOR',
  unit: 'defense',
  personnel: 'nickel',
  formation: '4-2-5_over',
  front: '4-2-5_over',
  coverage: 'cover_3',
  rule_profile: 'nfl',
  players: [{ id: 'WLB', position: 'WLB', start: { x: 55, y: 18 } }, { id: 'RB', position: 'RB', start: { x: 55, y: 35 } }],
  elements: [
    { id: 'FIT-WLB', kind: 'fit', type: 'spill', player_id: 'WLB', points: [{ x: 55, y: 18 }, { x: 50, y: 28 }], start_ms: 0, end_ms: 1200, timing: { start_ms: 0, end_ms: 1200, phases: [{ id: 'fit', label: 'Fit', start_ms: 0, end_ms: 1200 }] } },
    { id: 'READ-RB', kind: 'read', type: 'read_back', player_id: 'WLB', start_ms: 0, end_ms: 400 },
  ],
  timeline: { duration_ms: 3000 },
};

function inspectorProps() {
  return {
    design: DESIGN,
    selected: [{ kind: 'element' as const, id: 'FIT-WLB' }],
    tab: 'inspect' as const,
    dirty: true,
    comments: [],
    onTab: vi.fn(),
    onSelect: vi.fn(),
    onMeta: vi.fn(),
    onFieldContext: vi.fn(),
    onPlayer: vi.fn(),
    onElement: vi.fn(),
    onComment: vi.fn(),
    onRequestReview: vi.fn(),
    onPublish: vi.fn(),
    onBranch: vi.fn(),
    onCompare: vi.fn(),
    onMerge: vi.fn(),
  };
}

describe('DesignerInspector assignment graph controls', () => {
  it('exposes local adoption constraints for jurisdiction-dependent profiles', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} design={{ ...DESIGN, rule_profile: 'youth' }} />);
    fireEvent.change(screen.getByLabelText('Rule profile'), { target: { value: 'youth' } });
    fireEvent.change(screen.getByLabelText('Local rule source reference'), { target: { value: 'LEAGUE-RULEBOOK-2026' } });
    fireEvent.blur(screen.getByLabelText('Local rule source reference'));
    expect(props.onMeta).toHaveBeenCalledWith({ local_rule_source_ref: 'LEAGUE-RULEBOOK-2026' });
    fireEvent.change(screen.getByLabelText('Players on field'), { target: { value: '8' } });
    fireEvent.blur(screen.getByLabelText('Players on field'));
    expect(props.onMeta).toHaveBeenCalledWith({ local_rule_constraints: { players_on_field: 8 } });
  });

  it('authors targets, prerequisites, exclusivity, and synchronized timing', async () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} />);

    fireEvent.change(await screen.findByLabelText('Target player'), { target: { value: 'RB' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { target_player_id: 'RB' });

    fireEvent.click(screen.getByRole('checkbox', { name: /read_back/i }));
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { depends_on: ['READ-RB'] });

    fireEvent.click(screen.getByRole('checkbox', { name: /Exclusive responsibility/i }));
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { exclusive_assignment: true });

    fireEvent.change(screen.getByLabelText('Arrow / line meaning'), { target: { value: 'rush' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { arrow_style: 'rush' });
    fireEvent.change(screen.getByLabelText('Line treatment'), { target: { value: 'dashed' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { line_style: 'dashed' });
    fireEvent.change(screen.getByLabelText('Arrowheads'), { target: { value: 'both' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { arrow_ends: 'both' });
    fireEvent.change(screen.getByLabelText('Path geometry'), { target: { value: 'sharp' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', { path_mode: 'sharp' });
    fireEvent.change(screen.getByLabelText('Break angle'), { target: { value: 'inside' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', expect.objectContaining({ angle_preset: 'inside' }));
    fireEvent.change(screen.getByLabelText('Gap ownership'), { target: { value: 'left_b' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', expect.objectContaining({ gap_owner: 'left_b', gap: 'left_b', fit_gap: 'left_b' }));

    fireEvent.change(screen.getByLabelText('Defensive responsibility preset'), { target: { value: 'spill_fit' } });
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', expect.objectContaining({ type: 'spill', fit_rule: 'spill', phase: 'fit', arrow_style: 'fit' }));

    const end = screen.getByLabelText('End (ms)');
    fireEvent.change(end, { target: { value: '1800' } });
    fireEvent.blur(end);
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', expect.objectContaining({ end_ms: 1800, timing: expect.objectContaining({ end_ms: 1800 }) }));
  });

  it('authors snap alignment and jurisdiction-aware offensive eligibility data', () => {
    const props = inspectorProps();
    const offenseDesign = {
      ...DESIGN,
      unit: 'offense' as const,
      players: [{ id: 'LT', position: 'LT', alignment: { on_line: true, eligible: true, number: 72 }, start: { x: 44, y: 26 } }],
    };
    render(<DesignerInspector {...props} design={offenseDesign} selected={[{ kind: 'player', id: 'LT' }]} />);

    fireEvent.change(screen.getByLabelText('Jersey number'), { target: { value: '75' } });
    fireEvent.blur(screen.getByLabelText('Jersey number'));
    expect(props.onPlayer).toHaveBeenCalledWith('LT', { alignment: { on_line: true, eligible: true, number: 75 } });
    expect(screen.getByRole('alert', { name: /Eligibility review required/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('checkbox', { name: 'Reported eligible exception' }));
    expect(props.onPlayer).toHaveBeenCalledWith('LT', { alignment: { on_line: true, eligible: true, number: 72, reported_eligible: true } });
  });

  it('does not expose number-based exceptions for local non-NFL/NCAA profiles', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} design={{ ...DESIGN, unit: 'offense', rule_profile: 'high_school' }} selected={[{ kind: 'player', id: 'LT' }]} />);
    expect(screen.queryByRole('checkbox', { name: 'Reported eligible exception' })).not.toBeInTheDocument();
  });

  it('declares coverage-shell zones for server ownership checks', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} />);

    fireEvent.click(screen.getByRole('checkbox', { name: 'Deep middle' }));
    expect(props.onMeta).toHaveBeenCalledWith({ coverage_zones: ['deep_middle'] });
    fireEvent.click(screen.getByRole('checkbox', { name: 'Flat right' }));
    expect(props.onMeta).toHaveBeenCalledWith({ coverage_zones: ['flat_right'] });
  });

  it('links defensive exchange partners with an explicit role', () => {
    const props = inspectorProps();
    const design = { ...DESIGN, elements: [...DESIGN.elements!, { id: 'RUSH-DE', kind: 'rush', type: 'edge', player_id: 'RB', points: [{ x: 55, y: 35 }, { x: 60, y: 45 }] }] };
    render(<DesignerInspector {...props} design={design} selected={[{ kind: 'element', id: 'RUSH-DE' }]} />);

    fireEvent.change(screen.getByLabelText('Exchange partner'), { target: { value: 'FIT-WLB' } });
    expect(props.onElement).toHaveBeenCalledWith('RUSH-DE', expect.objectContaining({ exchange_with: 'FIT-WLB', phase: 'exchange' }));
    expect(props.onElement).toHaveBeenCalledWith('FIT-WLB', expect.objectContaining({ exchange_with: 'RUSH-DE', phase: 'exchange' }));
  });

  it('shows live unsaved-draft findings and locates the affected object', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} tab="validate" legality={{
      design_id: DESIGN.id,
      rule_profile: 'nfl',
      status: 'invalid',
      issues: [{ code: 'ASSIGNMENT-DEPENDENCY-CYCLE', message: 'Dependency cycle detected.', severity: 'error', path: 'elements[0].depends_on', suggestion: 'Remove one dependency.' }],
      overrides: [],
      draft: true,
      persisted: false,
      draft_checksum: '1234567890abcdef',
      normalized_design: DESIGN,
      assignment_graph: { version: '1.0', nodes: [], edges: [], findings: [], summary: { node_count: 2, edge_count: 1, blocking_count: 1, warning_count: 0 } },
    }} />);
    expect(screen.getByText('Live unsaved draft checked')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText(/Remove one dependency/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Locate on canvas' }));
    expect(props.onSelect).toHaveBeenCalledWith({ kind: 'element', id: 'FIT-WLB' });
    expect(props.onTab).toHaveBeenCalledWith('inspect');
  });

  it('expands exact base, target, and branch values for a merge conflict', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} tab="review" mergeConflict={{ status: 'conflict', branch_id: 'BR-1', conflicts: [{ path: 'elements.FIT-WLB.type', base: 'fit', target: 'spill', branch: 'box', message: 'Both branches changed the assignment.' }] }} />);
    expect(screen.getByText('Merge paused for human resolution')).toBeInTheDocument();
    fireEvent.click(screen.getByText('elements.FIT-WLB.type'));
    expect(screen.getByText('Base')).toBeVisible();
    expect(screen.getByText('spill')).toBeVisible();
    expect(screen.getByText('box')).toBeVisible();
    expect(screen.getByText('Both branches changed the assignment.')).toBeVisible();
  });
});
