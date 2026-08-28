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
    expect(screen.getByRole('alert', { name: /^Eligibility review required$/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('checkbox', { name: 'Reported eligible exception' }));
    expect(props.onPlayer).toHaveBeenCalledWith('LT', { alignment: { on_line: true, eligible: true, number: 72, reported_eligible: true } });
  });

  it('does not expose number-based exceptions for local non-NFL/NCAA profiles', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} design={{ ...DESIGN, unit: 'offense', rule_profile: 'high_school' }} selected={[{ kind: 'player', id: 'LT' }]} />);
    expect(screen.queryByRole('checkbox', { name: 'Reported eligible exception' })).not.toBeInTheDocument();
  });

  it('summarizes offensive personnel eligibility exceptions across the whole play', () => {
    const props = inspectorProps();
    const offenseDesign = {
      ...DESIGN,
      unit: 'offense' as const,
      players: [
        { id: 'LT', position: 'LT', alignment: { eligible: true, number: 72 }, start: { x: 44, y: 26 } },
        { id: 'RT', position: 'RT', alignment: { eligible: true, number: 74, reported_eligible: true }, start: { x: 56, y: 26 } },
      ],
    };
    render(<DesignerInspector {...props} design={offenseDesign} selected={[]} />);

    expect(screen.getByRole('alert', { name: 'Personnel eligibility review required' })).toHaveTextContent('1 personnel finding require review');
    fireEvent.click(screen.getByRole('button', { name: /LT.*#72/i }));
    expect(props.onSelect).toHaveBeenCalledWith({ kind: 'player', id: 'LT' });
  });

  it('shows a clean personnel legality state when no exception is present', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} design={{ ...DESIGN, unit: 'offense', players: [{ id: 'LT', position: 'LT', alignment: { eligible: true, number: 72, reported_eligible: true } }] }} selected={[]} />);
    expect(screen.getByRole('status')).toHaveTextContent('No number-based eligibility exceptions detected.');
  });

  it('flags duplicate offensive jersey numbers and locates the first affected player', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} design={{ ...DESIGN, unit: 'offense', players: [
      { id: 'X', position: 'X', alignment: { number: 11 } },
      { id: 'Y', position: 'Y', alignment: { number: 11 } },
    ] }} selected={[]} />);
    expect(screen.getByRole('alert', { name: 'Personnel eligibility review required' })).toHaveTextContent('Duplicate jersey number #11');
    fireEvent.click(screen.getByRole('button', { name: /Duplicate jersey number #11/i }));
    expect(props.onSelect).toHaveBeenCalledWith({ kind: 'player', id: 'X' });
  });

  it('supports exact coordinate editing for alternate route handles', async () => {
    const props = inspectorProps();
    const routeDesign = {
      ...DESIGN,
      unit: 'offense' as const,
      players: [{ id: 'X', position: 'X', start: { x: 30, y: 26 } }],
      elements: [{ id: 'ROUTE-X', kind: 'route', type: 'choice', player_id: 'X', points: [{ x: 30, y: 26 }, { x: 30, y: 12 }], branches: [{ id: 'BRANCH-X', label: 'Deep cross', condition: 'If leverage changes', points: [{ x: 30, y: 12 }, { x: 48, y: 12 }] }] }],
    };
    render(<DesignerInspector {...props} design={routeDesign} selected={[{ kind: 'element', id: 'ROUTE-X' }]} />);
    fireEvent.click(await screen.findByText('Precise path geometry · 2 handles'));
    const xInput = await screen.findByLabelText('Path Deep cross handle 2 X');
    fireEvent.change(xInput, { target: { value: '44' } });
    fireEvent.blur(xInput);
    expect(props.onElement).toHaveBeenCalledWith('ROUTE-X', expect.objectContaining({ branches: [expect.objectContaining({ id: 'BRANCH-X', points: [{ x: 30, y: 12 }, { x: 44, y: 12 }] })] }));
  });

  it('inserts a midpoint handle while keeping branch geometry editable', async () => {
    const props = inspectorProps();
    const routeDesign = {
      ...DESIGN,
      unit: 'offense' as const,
      elements: [{ id: 'ROUTE-X', kind: 'route', type: 'choice', points: [{ x: 30, y: 26 }, { x: 30, y: 12 }], branches: [{ id: 'BRANCH-X', label: 'Convert', condition: 'If squat', points: [{ x: 30, y: 12 }, { x: 48, y: 12 }] }] }],
    };
    render(<DesignerInspector {...props} design={routeDesign} selected={[{ kind: 'element', id: 'ROUTE-X' }]} />);
    fireEvent.click(await screen.findByText('Precise path geometry · 2 handles'));
    fireEvent.click(screen.getAllByRole('button', { name: 'Insert after' })[0]);
    expect(props.onElement).toHaveBeenCalledWith('ROUTE-X', expect.objectContaining({ branches: [expect.objectContaining({ points: [{ x: 30, y: 12 }, { x: 39, y: 12 }, { x: 48, y: 12 }] })] }));
  });

  it('surfaces incomplete blocking relationships in the Checks panel', () => {
    const props = inspectorProps();
    render(<DesignerInspector {...props} tab="validate" design={{ ...DESIGN, unit: 'offense', elements: [{ id: 'COMBO', kind: 'block', type: 'combo', blocking_primitive: 'combo' }] }} />);
    expect(screen.getByText('COMBO_PARTNER_REQUIRED')).toBeInTheDocument();
    expect(screen.getByText(/Choose the adjacent blocker or partner assignment/)).toBeInTheDocument();
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
