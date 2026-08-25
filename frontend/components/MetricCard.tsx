export function MetricCard({ label, value, detail, accent = "lime" }: { label: string; value: string; detail: string; accent?: "lime" | "blue" | "orange" }) {
  return (
    <article className={`metric-card metric-${accent}`}>
      <p className="eyebrow">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}
