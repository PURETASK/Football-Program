import { CircleHelp, type LucideIcon } from 'lucide-react';
import { useId } from 'react';

export interface DescriptionBoxProps {
  title: string;
  description: string;
  howItWorks?: string;
  audience?: string;
  outcome?: string;
  icon?: LucideIcon;
  compact?: boolean;
  tone?: 'blue' | 'cyan' | 'amber' | 'violet' | 'green';
  label?: string;
}

export function DescriptionBox({
  title,
  description,
  howItWorks,
  audience,
  outcome,
  icon: Icon = CircleHelp,
  compact = false,
  tone = 'blue',
  label = 'System description',
}: DescriptionBoxProps) {
  const headingId = useId();
  const Heading = compact ? 'h3' : 'h2';

  return (
    <section className={`description-box description-box--${tone}${compact ? ' description-box--compact' : ''}`} aria-labelledby={headingId}>
      <span className="description-box__icon" aria-hidden="true"><Icon size={compact ? 17 : 21} /></span>
      <div className="description-box__body">
        <p className="description-box__label">{label}</p>
        <Heading id={headingId}>{title}</Heading>
        <p className="description-box__description">{description}</p>
        {howItWorks || audience || outcome ? (
          <dl className="description-box__details">
            {howItWorks ? <div><dt>How it works</dt><dd>{howItWorks}</dd></div> : null}
            {audience ? <div><dt>Used by</dt><dd>{audience}</dd></div> : null}
            {outcome ? <div><dt>Produces</dt><dd>{outcome}</dd></div> : null}
          </dl>
        ) : null}
      </div>
    </section>
  );
}
