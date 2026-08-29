import { ArrowRight, BookOpen, MoveUpRight, PlusCircle, Sparkles } from 'lucide-react';

import type { PlayAsset, PlayDesign, PlayPlayer, PlayTemplate } from '../types';
import { assetName, positionAssetFit, positionAssetOptions, positionProfile, positionTemplateOptions } from './positionOptions';

function optionGlyph(kind: string): string {
  if (kind === 'block' || kind === 'protection') return '⇢';
  if (kind === 'motion') return '↝';
  if (kind === 'run') return '↗';
  if (['coverage', 'rotation', 'fit'].includes(kind)) return '◇';
  if (['rush', 'stunt'].includes(kind)) return '➤';
  if (['read', 'check', 'teaching'].includes(kind)) return 'A';
  return '╱';
}

function optionDescription(asset: PlayAsset): string {
  return asset.description ?? asset.accessibility ?? 'Reusable football assignment building block.';
}

export function PositionToolkit({ player, design, assets, templates, onChooseAsset, onApplyTemplate, onMaterializeAsset }: {
  player: PlayPlayer;
  design: PlayDesign;
  assets: PlayAsset[];
  templates: PlayTemplate[];
  onChooseAsset: (asset: PlayAsset) => void;
  onApplyTemplate: (template: PlayTemplate, mode: 'replace' | 'layer') => void;
  onMaterializeAsset?: (asset: PlayAsset) => void;
}) {
  const profile = positionProfile(player, design.unit);
  const options = positionAssetOptions(player, design, assets).slice(0, 8);
  const suggestedTemplates = positionTemplateOptions(player, design, templates).slice(0, 3);
  const position = player.position ?? player.role ?? player.id;

  return (
    <section className="position-toolkit" aria-labelledby="position-toolkit-title">
      <header className="position-toolkit__header">
        <div><span className="designer-kicker"><Sparkles size={11} /> Position toolkit</span><h3 id="position-toolkit-title">{position} options</h3></div>
        <span className="position-toolkit__badge">{profile.family}</span>
      </header>
      <p className="position-toolkit__description">{profile.description} Select an option to activate it, then draw from this player on the field.</p>
      <div className="position-toolkit__options" aria-label={`${position} recommended assignment options`}>
        {options.map((asset) => { const fit = positionAssetFit(asset, design); const detailsId = `position-option-${asset.id}-details`; const details = [optionDescription(asset), ...(fit.reasons.length ? [`Review notes: ${fit.reasons.join(' ')}`] : ['Compatible with the current play context.'])].join(' '); return <div className={`position-option${fit.compatible ? '' : ' is-review'}`} key={asset.id} title={details}>
          <span className={`position-option__glyph position-option__glyph--${asset.kind}`} aria-hidden="true">{optionGlyph(asset.category ?? asset.kind)}</span>
          <span className="position-option__copy"><strong>{assetName(asset)}</strong><small>{asset.category ?? asset.kind} · {asset.default_timing_ms ? `${(asset.default_timing_ms / 1000).toFixed(1)}s guide` : 'custom timing'} · {fit.compatible ? 'compatible' : 'review fit'}</small></span>
          <span className="position-option__actions"><button type="button" className="position-option__draw" onClick={() => onChooseAsset(asset)} aria-describedby={detailsId} aria-label={`Draw ${assetName(asset)} from ${position}`}><ArrowRight size={13} aria-hidden="true" /></button>{onMaterializeAsset ? <button type="button" className="position-option__add" onClick={() => onMaterializeAsset(asset)} aria-describedby={detailsId} aria-label={`Add ${assetName(asset)} starting action for ${position}`} title="Add an editable starting action"><PlusCircle size={13} aria-hidden="true" /></button> : null}</span>
          <span className="sr-only" id={detailsId}>{details}</span>
        </div>; })}
      </div>
      {!options.length ? <p className="position-toolkit__empty">No compatible options are loaded for this position yet. Use the full asset library to author a custom assignment.</p> : null}
      {suggestedTemplates.length ? <div className="position-toolkit__templates"><div className="position-toolkit__subhead"><span><BookOpen size={13} /> Suggested templates</span><small>Layer into this call</small></div>{suggestedTemplates.map((template) => <button type="button" className="position-template" key={template.id} onClick={() => onApplyTemplate(template, 'layer')}><span><MoveUpRight size={13} /></span><span><strong>{template.name ?? template.id}</strong><small>{template.layer?.replaceAll('_', ' ') ?? 'reusable concept'} · {template.description ?? 'Reusable football layer'}</small></span><ArrowRight size={13} aria-hidden="true" /></button>)}</div> : null}
    </section>
  );
}
