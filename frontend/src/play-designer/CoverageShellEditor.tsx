import { coverageShellBoxes, COVERAGE_SHELL_OPTIONS } from './coverageShell';

interface CoverageShellEditorProps {
  zones: string[];
  onChange: (zones: string[]) => void;
}

export function CoverageShellEditor({ zones, onChange }: CoverageShellEditorProps) {
  const active = new Set(coverageShellBoxes(zones).map((box) => box.id));
  const toggle = (id: string) => onChange(active.has(id) ? zones.filter((zone) => zone !== id) : [...zones, id]);
  return <div className="coverage-shell-authoring" data-testid="coverage-shell-authoring">
    <div className="coverage-shell-authoring__header"><span><strong>Interactive shell map</strong><small>Click a region to declare its coverage responsibility.</small></span><span className="coverage-shell-authoring__count" aria-live="polite">{active.size} declared</span></div>
    <svg className="coverage-shell-authoring__map" viewBox="0 0 100 40" role="group" aria-label="Interactive defensive coverage shell map">
      <rect x="0.5" y="0.5" width="99" height="39" rx="1.5" className="coverage-shell-authoring__field" />
      <line x1="0" y1="14.8" x2="100" y2="14.8" className="coverage-shell-authoring__divider" /><line x1="0" y1="27.2" x2="100" y2="27.2" className="coverage-shell-authoring__divider" />
      {COVERAGE_SHELL_OPTIONS.map((box) => { const selected = active.has(box.id); return <g key={box.id} className={selected ? 'coverage-shell-authoring__zone is-active' : 'coverage-shell-authoring__zone'}><rect x={box.x} y={box.y} width={box.width} height={box.height} rx="1" role="button" tabIndex={0} aria-label={`${box.label} coverage zone`} aria-pressed={selected} onClick={() => toggle(box.id)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); toggle(box.id); } }} /><text x={box.x + box.width / 2} y={box.y + box.height / 2 + 1} textAnchor="middle">{box.label}</text></g>; })}
    </svg>
    <div className="coverage-shell-authoring__legend"><span><i className="is-active" /> Declared</span><span><i /> Available</span></div>
  </div>;
}
