export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? 'brand brand--compact' : 'brand'}>
      <svg className="brand__mark" viewBox="0 0 48 48" role="img" aria-label="NFL FIDOS">
        <path d="M24 3C13 3 5 12 5 24s8 21 19 21 19-9 19-21S35 3 24 3Z" fill="currentColor" />
        <path
          d="M16 14c5 2 11 2 16 0M14 21c6 2 14 2 20 0M16 29c5 2 11 2 16 0M20 36c3 1 5 1 8 0"
          fill="none"
          stroke="var(--brand-route)"
          strokeLinecap="round"
          strokeWidth="3"
        />
        <path d="M24 9v30" stroke="var(--brand-seam)" strokeLinecap="round" strokeWidth="2" />
      </svg>
      <span className="brand__copy">
        <strong>FIDOS</strong>
        <span>Football Intelligence OS</span>
      </span>
    </div>
  );
}
