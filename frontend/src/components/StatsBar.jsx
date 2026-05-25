// frontend/src/components/StatsBar.jsx
// --------------------------------------
// Top bar showing aggregate stats: total inspected, pass rate,
// average quality score, and top defect type.

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      flex: 1,
      padding: "14px 18px",
      borderRadius: "10px",
      background: "white",
      border: "1px solid #e5e7eb",
      minWidth: "120px",
    }}>
      <p style={{ margin: "0 0 2px", fontSize: "12px", color: "#6b7280", fontWeight: 500 }}>
        {label}
      </p>
      <p style={{ margin: 0, fontSize: "22px", fontWeight: 600, color: color || "#111827" }}>
        {value}
      </p>
      {sub && (
        <p style={{ margin: "2px 0 0", fontSize: "12px", color: "#9ca3af" }}>{sub}</p>
      )}
    </div>
  );
}

function qualityColor(score) {
  if (score == null) return "#111827";
  if (score >= 90)   return "#16a34a";
  if (score >= 75)   return "#2563eb";
  if (score >= 60)   return "#d97706";
  if (score >= 40)   return "#ea580c";
  return "#dc2626";
}

export default function StatsBar({ stats }) {
  if (!stats || stats.total === 0) {
    return (
      <div style={{
        padding: "14px 18px",
        borderRadius: "10px",
        background: "white",
        border: "1px solid #e5e7eb",
        color: "#9ca3af",
        fontSize: "14px",
        textAlign: "center",
      }}>
        Stats will appear here after your first inspection.
      </div>
    );
  }

  // Find the most common defect type
  const breakdown = stats.defect_breakdown || {};
  const topDefect = Object.entries(breakdown)
    .sort((a, b) => b[1] - a[1])[0];

  return (
    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
      <StatCard
        label="Total inspected"
        value={stats.total}
      />
      <StatCard
        label="Pass rate"
        value={`${stats.pass_rate}%`}
        sub={`${stats.passed} passed, ${stats.failed} failed`}
        color={stats.pass_rate >= 80 ? "#15803d" : "#b91c1c"}
      />
      <StatCard
        label="Avg quality score"
        value={stats.avg_quality_score != null ? stats.avg_quality_score.toFixed(1) : "—"}
        sub="out of 100"
        color={qualityColor(stats.avg_quality_score)}
      />
      <StatCard
        label="Most common defect"
        value={topDefect ? topDefect[0].replace(/_/g, " ") : "None"}
        sub={topDefect ? `${topDefect[1]} instance${topDefect[1] !== 1 ? "s" : ""}` : ""}
        color="#7c3aed"
      />
    </div>
  );
}
