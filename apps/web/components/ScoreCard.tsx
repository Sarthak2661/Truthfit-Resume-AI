export function ScoreCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <div className="card metric">
      <span className="section-label">{label}</span>
      <strong>{value}</strong>
      {detail ? <span className="muted">{detail}</span> : null}
    </div>
  );
}
