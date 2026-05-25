// frontend/src/components/SeverityReport.jsx
// -------------------------------------------
// Displays the board quality score gauge, severity breakdown,
// recommendation text, and a "Download Report" button.

import { getReport } from "../api/client";

// ── Grade colour mapping ──────────────────────────────────────────────────────
const GRADE_CONFIG = {
  A: { color: "#16a34a", bg: "#f0fdf4", border: "#bbf7d0", label: "Excellent" },
  B: { color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe", label: "Good" },
  C: { color: "#d97706", bg: "#fffbeb", border: "#fde68a", label: "Marginal" },
  D: { color: "#ea580c", bg: "#fff7ed", border: "#fed7aa", label: "Poor" },
  F: { color: "#dc2626", bg: "#fef2f2", border: "#fecaca", label: "Rejected" },
};

// ── Arc gauge helpers ─────────────────────────────────────────────────────────
function ScoreGauge({ score, grade }) {
  const cfg  = GRADE_CONFIG[grade] || GRADE_CONFIG["F"];
  const pct  = Math.max(0, Math.min(100, score ?? 0));
  const r    = 54;                        // circle radius
  const circ = 2 * Math.PI * r;          // full circumference
  // We show a 270° arc (from 225° to 495°). Offset so the "empty" part is at the bottom.
  const arcLen   = circ * 0.75;          // 270/360 * circumference
  const filled   = arcLen * (pct / 100);
  const dashArr  = `${filled} ${circ - filled}`;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
      <svg width="140" height="140" viewBox="0 0 128 128">
        {/* Track arc */}
        <circle
          cx="64" cy="64" r={r}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="10"
          strokeDasharray={`${arcLen} ${circ - arcLen}`}
          strokeDashoffset={circ * 0.125}   /* rotate start to ~225° */
          strokeLinecap="round"
          transform="rotate(-225 64 64)"
        />
        {/* Filled arc */}
        <circle
          cx="64" cy="64" r={r}
          fill="none"
          stroke={cfg.color}
          strokeWidth="10"
          strokeDasharray={dashArr}
          strokeDashoffset={circ * 0.125}
          strokeLinecap="round"
          transform="rotate(-225 64 64)"
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
        {/* Score text */}
        <text x="64" y="60" textAnchor="middle" fontSize="22" fontWeight="700" fill={cfg.color}>
          {score != null ? score.toFixed(1) : "—"}
        </text>
        {/* Grade */}
        <text x="64" y="80" textAnchor="middle" fontSize="13" fontWeight="600" fill="#6b7280">
          Grade {grade ?? "—"}
        </text>
      </svg>
      <p style={{ margin: 0, fontSize: "12px", color: cfg.color, fontWeight: 600 }}>
        {cfg.label}
      </p>
    </div>
  );
}

// ── Severity pill ─────────────────────────────────────────────────────────────
const SEVERITY_PILL_CONFIG = {
  critical: { bg: "#fef2f2", color: "#dc2626", border: "#fecaca", emoji: "🔴" },
  major:    { bg: "#fff7ed", color: "#ea580c", border: "#fed7aa", emoji: "🟠" },
  minor:    { bg: "#fffbeb", color: "#ca8a04", border: "#fde68a", emoji: "🟡" },
};

function SeverityPill({ level, count }) {
  const cfg = SEVERITY_PILL_CONFIG[level];
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "6px",
      padding: "8px 14px",
      borderRadius: "999px",
      background: cfg.bg,
      border: `1px solid ${cfg.border}`,
      fontSize: "13px",
      fontWeight: 600,
      color: cfg.color,
    }}>
      <span>{cfg.emoji}</span>
      <span style={{ fontSize: "18px", fontWeight: 700 }}>{count}</span>
      <span style={{ textTransform: "capitalize" }}>{level}</span>
    </div>
  );
}

// ── Download helper ───────────────────────────────────────────────────────────
async function downloadReport(inspectionId, filename) {
  try {
    const report = await getReport(inspectionId);
    const blob   = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url    = URL.createObjectURL(blob);
    const a      = document.createElement("a");
    a.href       = url;
    a.download   = `pcb_report_${inspectionId}_${filename.replace(/\.[^.]+$/, "")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("Failed to download report: " + e.message);
  }
}

// ── Main component ────────────────────────────────────────────────────────────
export default function SeverityReport({ result }) {
  if (!result || result.quality_score == null) return null;

  const {
    id,
    filename,
    quality_score,
    grade,
    severity_summary,
    recommendation,
  } = result;

  const summary = severity_summary || { critical: 0, major: 0, minor: 0 };
  const gradeCfg = GRADE_CONFIG[grade] || GRADE_CONFIG["F"];

  return (
    <div style={{
      marginTop: "16px",
      borderRadius: "12px",
      border: `1px solid ${gradeCfg.border}`,
      background: gradeCfg.bg,
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        padding: "12px 16px",
        borderBottom: `1px solid ${gradeCfg.border}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <span style={{ fontWeight: 600, fontSize: "14px", color: "#374151" }}>
          📋 Board Quality Report
        </span>
        {id && (
          <button
            onClick={() => downloadReport(id, filename || "board")}
            style={{
              padding: "5px 12px",
              borderRadius: "6px",
              border: "1px solid #d1d5db",
              background: "white",
              fontSize: "12px",
              fontWeight: 500,
              color: "#374151",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "5px",
              transition: "background 0.15s",
            }}
            onMouseEnter={e => e.currentTarget.style.background = "#f9fafb"}
            onMouseLeave={e => e.currentTarget.style.background = "white"}
          >
            ⬇ Download JSON
          </button>
        )}
      </div>

      {/* Body */}
      <div style={{ padding: "16px", display: "flex", gap: "24px", flexWrap: "wrap", alignItems: "center" }}>

        {/* Gauge */}
        <ScoreGauge score={quality_score} grade={grade} />

        {/* Right side: pills + recommendation */}
        <div style={{ flex: 1, minWidth: "180px", display: "flex", flexDirection: "column", gap: "14px" }}>
          {/* Severity pills */}
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <SeverityPill level="critical" count={summary.critical} />
            <SeverityPill level="major"    count={summary.major}    />
            <SeverityPill level="minor"    count={summary.minor}    />
          </div>

          {/* Recommendation */}
          <div style={{
            padding: "10px 14px",
            borderRadius: "8px",
            background: "white",
            border: `1px solid ${gradeCfg.border}`,
            fontSize: "13px",
            color: "#374151",
            lineHeight: "1.5",
          }}>
            <span style={{ fontWeight: 600, color: gradeCfg.color }}>Recommendation: </span>
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
}
