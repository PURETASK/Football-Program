import { describe, expect, it } from 'vitest';

import type { PlayDesign } from '../types';
import { offensiveBlockingIssues } from './offensiveBlocking';

const DESIGN: PlayDesign = {
  id: 'BLOCK-TEST',
  unit: 'offense',
  players: [{ id: 'OL-1', position: 'LG' }],
  elements: [],
};

describe('offensive blocking diagnostics', () => {
  it('requires targets for pull and combo relationships', () => {
    const issues = offensiveBlockingIssues({ ...DESIGN, elements: [
      { id: 'PULL', kind: 'block', type: 'pull', blocking_primitive: 'pull' },
      { id: 'COMBO', kind: 'block', type: 'combo', blocking_primitive: 'combo' },
    ] });
    expect(issues.map((issue) => issue.code)).toEqual(expect.arrayContaining(['BLOCKING_TARGET_REQUIRED', 'COMBO_PARTNER_REQUIRED', 'COMBO_TARGET_REQUIRED']));
  });

  it('rejects invalid references and self-targeting as blocking errors', () => {
    const issues = offensiveBlockingIssues({ ...DESIGN, elements: [
      { id: 'BLOCK', kind: 'block', blocking_primitive: 'base', block_target_element_id: 'BLOCK' },
      { id: 'BROKEN', kind: 'block', blocking_primitive: 'base', block_target_element_id: 'MISSING', block_partner_element_id: 'MISSING-PARTNER' },
    ] });
    expect(issues.filter((issue) => issue.severity === 'error').map((issue) => issue.code)).toEqual(expect.arrayContaining(['BLOCKING_SELF_REFERENCE', 'BLOCKING_TARGET_MISSING', 'BLOCKING_PARTNER_MISSING']));
  });

  it('requires screen protection mode for a screen release primitive', () => {
    const issues = offensiveBlockingIssues({ ...DESIGN, elements: [{ id: 'SCREEN', kind: 'block', blocking_primitive: 'screen_release', protection_mode: 'man' }] });
    expect(issues).toEqual(expect.arrayContaining([expect.objectContaining({ code: 'SCREEN_PROTECTION_MODE', severity: 'warning' })]));
  });

  it('does not apply offensive blocking diagnostics to defensive designs', () => {
    expect(offensiveBlockingIssues({ ...DESIGN, unit: 'defense', elements: [{ id: 'RUSH', kind: 'rush', blocking_primitive: 'combo' }] })).toEqual([]);
  });
});
