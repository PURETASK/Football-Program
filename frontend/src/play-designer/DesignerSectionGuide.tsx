import { CircleHelp } from 'lucide-react';

export function DesignerSectionGuide({ title, description }: { title: string; description: string }) {
  return (
    <section className="designer-section-guide" aria-label={`${title} description`}>
      <CircleHelp aria-hidden="true" size={14} />
      <div><strong>{title}</strong><span>{description}</span></div>
    </section>
  );
}
