import type { PlayAsset, PlayDesign, PlayPlayer, PlayTemplate } from '../types';

export interface PositionProfile {
  family: string;
  title: string;
  description: string;
  preferredCategories: string[];
  templateLayers: string[];
}

export interface PositionAssetFit {
  compatible: boolean;
  reasons: string[];
}

const OFFENSE_PROFILES: Array<{ tokens: string[]; profile: PositionProfile }> = [
  { tokens: ['QB', 'QUARTERBACK'], profile: { family: 'quarterback', title: 'Quarterback toolkit', description: 'Reads, checks, movement, and ball-carrier actions that start with the quarterback.', preferredCategories: ['teaching', 'check', 'run', 'motion', 'route'], templateLayers: ['run_concept', 'route_concept', 'protection', 'check'] } },
  { tokens: ['LT', 'LG', 'C', 'RG', 'RT', 'OL', 'OT', 'OG', 'CENTER', 'GUARD', 'TACKLE'], profile: { family: 'offensive-line', title: 'Offensive line toolkit', description: 'Protection, leverage, combination, pull, and run-game responsibilities for the front.', preferredCategories: ['protection', 'block', 'run', 'teaching', 'check'], templateLayers: ['protection', 'run_concept'] } },
  { tokens: ['RB', 'TB', 'HB', 'FB', 'F', 'BACK'], profile: { family: 'backfield', title: 'Backfield toolkit', description: 'Run tracks, pass-game releases, motion, protection, and read responsibilities.', preferredCategories: ['run', 'route', 'motion', 'block', 'check', 'teaching'], templateLayers: ['run_concept', 'route_concept', 'protection'] } },
  { tokens: ['WR', 'X', 'Z', 'H', 'SLOT', 'TE', 'U', 'Y', 'RECEIVER', 'TIGHT END'], profile: { family: 'eligible', title: 'Eligible receiver toolkit', description: 'Route stems, releases, motions, blocking surfaces, and adjustment teaching cues.', preferredCategories: ['route', 'motion', 'block', 'check', 'read', 'teaching'], templateLayers: ['route_concept', 'run_concept', 'check'] } },
];

const DEFENSE_PROFILES: Array<{ tokens: string[]; profile: PositionProfile }> = [
  { tokens: ['DE', 'DT', 'NT', 'DL', 'EDGE', 'TACKLE', 'NOSE'], profile: { family: 'defensive-front', title: 'Defensive front toolkit', description: 'Front alignment, rush paths, stunts, fits, and read keys for the defensive line.', preferredCategories: ['front', 'rush', 'stunt', 'fit', 'read', 'teaching'], templateLayers: ['front', 'pressure_layer', 'coverage_layer'] } },
  { tokens: ['LB', 'ILB', 'MLB', 'WLB', 'WILL', 'SAM', 'MIKE', 'OLB', 'JACK', 'BUCK', 'LINEBACKER'], profile: { family: 'linebacker', title: 'Linebacker toolkit', description: 'Run fits, pressure paths, coverage drops, rotations, and key-reading instructions.', preferredCategories: ['fit', 'coverage', 'rush', 'stunt', 'rotation', 'read', 'check', 'teaching'], templateLayers: ['pressure_layer', 'coverage_layer', 'front'] } },
  { tokens: ['CB', 'NB', 'S', 'FS', 'SS', 'DB', 'SAFETY', 'CORNER', 'NICKEL'], profile: { family: 'secondary', title: 'Secondary toolkit', description: 'Coverage techniques, rotations, leverage, pressure, and communication checks.', preferredCategories: ['coverage', 'rotation', 'fit', 'rush', 'read', 'check', 'teaching'], templateLayers: ['coverage_layer', 'pressure_layer'] } },
];

const GENERIC_PROFILE: PositionProfile = { family: 'general', title: 'Player toolkit', description: 'Position-aware assignment, movement, teaching, and communication options for this player.', preferredCategories: ['route', 'motion', 'run', 'block', 'coverage', 'rush', 'stunt', 'fit', 'read', 'check', 'teaching'], templateLayers: ['route_concept', 'run_concept', 'protection', 'coverage_layer', 'pressure_layer'] };

function positionTokens(player: PlayPlayer): string[] {
  return [player.position, player.role, player.alignment_key].filter(Boolean).map((value) => String(value).trim().toUpperCase());
}

export function positionProfile(player: PlayPlayer, unit: PlayDesign['unit']): PositionProfile {
  const tokens = positionTokens(player);
  const profiles = unit === 'defense' ? DEFENSE_PROFILES : OFFENSE_PROFILES;
  return profiles.find(({ tokens: candidates }) => tokens.some((token) => candidates.includes(token)))?.profile ?? GENERIC_PROFILE;
}

export function assetName(asset: PlayAsset): string {
  return asset.display_name ?? asset.term.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/** Explain why an asset is or is not safe to suggest for the active play. */
export function positionAssetFit(asset: PlayAsset, design: PlayDesign): PositionAssetFit {
  const reasons: string[] = [];
  if (asset.unit !== design.unit && asset.unit !== 'shared') reasons.push(`Designed for ${asset.unit}.`);
  if (asset.compatible_formations?.length && design.formation && !asset.compatible_formations.includes(design.formation)) reasons.push(`Not cataloged for ${design.formation.replaceAll('_', ' ')}.`);
  if (asset.compatible_personnel?.length && design.personnel && !asset.compatible_personnel.includes(design.personnel)) reasons.push(`Not cataloged for ${design.personnel} personnel.`);
  if (asset.compatible_rule_profiles?.length && design.rule_profile && !asset.compatible_rule_profiles.includes(design.rule_profile)) reasons.push(`Not approved for ${design.rule_profile.replaceAll('_', ' ')} rules.`);
  if (asset.compatibility && !asset.compatibility.compatible) reasons.push(...asset.compatibility.reasons);
  if (!['active', 'approved'].includes(asset.status ?? 'active')) reasons.push(`Lifecycle state is ${asset.status}.`);
  return { compatible: reasons.length === 0, reasons: [...new Set(reasons)] };
}

export function positionAssetOptions(player: PlayPlayer, design: PlayDesign, assets: PlayAsset[]): PlayAsset[] {
  const profile = positionProfile(player, design.unit);
  return assets
    .filter((asset) => asset.kind !== 'formation' && asset.kind !== 'front' && asset.status !== 'retired' && asset.compatibility?.selectable !== false)
    .map((asset) => {
      const category = asset.category ?? asset.kind;
      const preference = profile.preferredCategories.indexOf(category);
      const unitFit = asset.unit === design.unit || asset.unit === 'shared' ? 30 : -80;
      const fit = positionAssetFit(asset, design);
      const compatibility = fit.compatible ? 20 : -25;
      const lifecycle = ['active', 'approved'].includes(asset.status ?? 'active') ? 10 : -30;
      return { asset, score: (preference < 0 ? -10 : 100 - preference * 8) + unitFit + compatibility + lifecycle };
    })
    .sort((left, right) => right.score - left.score || assetName(left.asset).localeCompare(assetName(right.asset)))
    .map(({ asset }) => asset);
}

export function positionTemplateOptions(player: PlayPlayer, design: PlayDesign, templates: PlayTemplate[]): PlayTemplate[] {
  const profile = positionProfile(player, design.unit);
  return templates
    .filter((template) => template.unit === design.unit || template.unit === 'shared')
    .map((template) => ({ template, score: profile.templateLayers.includes(template.layer ?? '') ? 100 : 10 }))
    .sort((left, right) => right.score - left.score || String(left.template.name ?? left.template.id).localeCompare(String(right.template.name ?? right.template.id)))
    .map(({ template }) => template);
}
