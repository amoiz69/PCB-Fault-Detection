// frontend/src/components/HistoryPanel.jsx
// ------------------------------------------
// Sidebar showing past inspections. Clicking one loads it back
// into the main panel via onSelect(inspection).
// Now also shows quality score and grade badge.

const GRADE_COLOR = {
  A: { color: "#16a34a", bg: "#f0fdf4" },
  B: { color: "#2563eb", bg: "#eff6ff" },
  C: { color: "#d97706", bg: "#fffbeb" },
  D: { color: "#ea580c", bg: "#fff7ed" },
  F: { color: "#dc2626", bg: "#fef2f2" },
};

export default function HistoryPanel({ history, onSelect, selectedId }) {
  if (!history || history.length === 0) {
    return (
      <div style={{ padding: "24px 16px", color: "#9ca3af", fontSize: "14px", textAlign: "center" }}>
        No inspections yet. Upload a PCB image to get started.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "8px" }}>
      {history.map((item) => {
        const isSelected = item.id === selectedId;
        const date = new Date(item.timestamp).toLocaleString();
        const gradeCfg = item.grade ? (GRADE_COLOR[item.grade] || GRADE_COLOR["F"]) : null;

        return (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "10px 12px",
              borderRadius: "8px",
              border: `1px solid ${isSelected ? "#6366f1" : "#e5e7eb"}`,
              background: isSelected ? "#eef2ff" : "white",
              cursor: "pointer",
              textAlign: "left",
              width: "100%",
              transition: "border-color 0.15s, background 0.15s",
            }}
          >
            {/* Pass/fail dot */}
            <span style={{
              width: "8px", height: "8px", borderRadius: "50%", flexShrink: 0,
              background: item.passed ? "#22c55e" : "#ef4444",
            }}/>

            <div style={{ flex: 1, minWidth: 0 }}>
              {/* Filename — truncate if long */}
              <p style={{
                margin: 0,
                fontSize: "13px",
                fontWeight: 500,
                color: "#111827",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}>
                {item.filename}
              </p>
              <p style={{ margin: "2px 0 0", fontSize: "12px", color: "#6b7280" }}>
                {date}
              </p>
            </div>

            {/* Quality score + grade badge (if available) */}
            {item.quality_score != null && gradeCfg ? (
              <div style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                flexShrink: 0,
                minWidth: "42px",
              }}>
                <span style={{
                  fontSize: "13px",
                  fontWeight: 700,
                  color: gradeCfg.color,
                }}>
                  {item.quality_score.toFixed(0)}
                </span>
                <span style={{
                  fontSize: "10px",
                  padding: "1px 5px",
                  borderRadius: "4px",
                  background: gradeCfg.bg,
                  color: gradeCfg.color,
                  fontWeight: 700,
                  border: `1px solid ${gradeCfg.color}30`,
                }}>
                  {item.grade}
                </span>
              </div>
            ) : (
              /* Fallback: defect count badge for old records */
              <span style={{
                fontSize: "12px",
                padding: "2px 7px",
                borderRadius: "999px",
                background: item.passed ? "#f0fdf4" : "#fef2f2",
                color: item.passed ? "#15803d" : "#b91c1c",
                fontWeight: 500,
                flexShrink: 0,
              }}>
                {item.defect_count === 0 ? "OK" : `${item.defect_count} defect${item.defect_count !== 1 ? "s" : ""}`}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
