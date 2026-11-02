export function ScoreCard({ label, value, detail, featured = false }: { label: string; value: string | number; detail?: string; featured?: boolean }) {
  return (
    <div className={`card metric ${featured ? "metric-featured" : ""}`}>
      <span className="section-label">{label}</span>
      <strong>{value}</strong>
      {detail ? <span className="muted">{detail}</span> : null}
    </div>
  );
}
