import { ArrowUpRight, GitBranch, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

import type { PlayDesign } from '../types';
import { FieldThumbnail } from './FieldThumbnail';
import { StatusPill, statusTone } from './StatusPill';

export function playDisplayName(design: PlayDesign): string {
  if (design.name?.trim()) return design.name.trim();
  const cleaned = design.id
    .replace(/^PD-/, '')
    .replace(/^(DEMO-)?(OFF|DEF|ST)-/, '')
    .replace(/-(COUNTER|BRANCH)$/i, ' $1')
    .replaceAll('-', ' ')
    .toLowerCase();
  return cleaned.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function PlayCard({ design, compact = false }: { design: PlayDesign; compact?: boolean }) {
  const name = playDisplayName(design);
  const validation = design.validation?.status ?? 'not checked';
  return (
    <article className={compact ? 'play-card play-card--compact' : 'play-card'}>
      <div className="play-card__visual">
        <FieldThumbnail design={design} name={name} />
        <span className={`unit-flag unit-flag--${design.unit}`}>{design.unit}</span>
        {design.parent_design_id ? (
          <span className="branch-flag" title="Branched play">
            <GitBranch size={13} /> Branch
          </span>
        ) : null}
      </div>
      <div className="play-card__body">
        <div className="play-card__status-row">
          <StatusPill label={(design.status ?? 'draft').replaceAll('_', ' ')} tone={statusTone(design.status)} />
          <span className="play-card__version">v{design.version ?? '0.1'}</span>
        </div>
        <h3>{name}</h3>
        <p>{design.personnel || 'Open'} personnel · {(design.formation || 'Unassigned formation').replaceAll('_', ' ')}</p>
        <div className="play-card__footer">
          <span className={validation === 'valid' ? 'validation-mark validation-mark--valid' : 'validation-mark'}>
            <ShieldCheck size={14} /> {validation}
          </span>
          <Link className="text-link" to={`/playbook/designer/${encodeURIComponent(design.id)}`}>
            Open designer <ArrowUpRight size={14} />
          </Link>
        </div>
      </div>
    </article>
  );
}
