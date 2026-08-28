import { Check, CircleAlert, Clock3, Radio } from 'lucide-react';

type StatusTone = 'good' | 'warning' | 'danger' | 'info' | 'neutral';

const ICONS = {
  good: Check,
  warning: Clock3,
  danger: CircleAlert,
  info: Radio,
  neutral: Radio,
};

export function StatusPill({ label, tone = 'neutral' }: { label: string; tone?: StatusTone }) {
  const Icon = ICONS[tone];
  return (
    <span className={`status-pill status-pill--${tone}`}>
      <Icon aria-hidden="true" size={12} strokeWidth={2.5} />
      {label}
    </span>
  );
}

export function statusTone(status?: string): StatusTone {
  const normalized = status?.toLowerCase() ?? '';
  if (['published', 'approved', 'active', 'valid', 'ready', 'ready_for_bundle', 'operational'].includes(normalized)) return 'good';
  if (['under_review', 'pending', 'draft', 'queued', 'needs_review'].includes(normalized)) return 'warning';
  if (['blocked', 'invalid', 'failed', 'rejected'].includes(normalized)) return 'danger';
  return 'neutral';
}
