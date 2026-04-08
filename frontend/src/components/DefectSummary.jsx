// frontend/src/components/DefectSummary.jsx
// -------------------------------------------
// Shows the verdict (PASS / FAIL) and a list of all detected defects
// with their class, confidence, and a colour swatch.

export default function DefectSummary({ result }) {
  if (!result) return null;

  const { passed, defect_count, confidence_avg, detections } = result;

  return (
    <div style={{ marginTop: "16px" }}>

      {/* Verdict banner */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "10px",
        padding: "12px 16px",
        borderRadius: "8px",
        background: passed ? "#f0fdf4" : "#fef2f2",
        border: `1px solid ${passed ? "#bbf7d0" : "#fecaca"}`,
        marginBottom: "16px",
      }}>
        <span style={{ fontSize: "22px" }}>{passed ? "✅" : "❌"}</span>
        <div>
          <p style={{
            margin: 0,
            fontWeight: 600,
            color: passed ? "#15803d" : "#b91c1c",
            fontSize: "16px",
          }}>
            {passed ? "PASS — No defects detected" : `FAIL — ${defect_count} defect${defect_count !== 1 ? "s" : ""} found`}
          </p>
          {confidence_avg && (
            <p style={{ margin: "2px 0 0", fontSize: "13px", color: "#6b7280" }}>
              Avg confidence: {(confidence_avg * 100).toFixed(1)}%
            </p>
          )}
        </div>
      </div>

      {/* Defect list */}
      {detections.length > 0 && (
        <div>
          <p style={{ fontWeight: 500, fontSize: "14px", color: "#374151", marginBottom: "8px" }}>
            Detected defects
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {detections.map((det, i) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "8px 12px",
                borderRadius: "6px",
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                fontSize: "14px",
              }}>
                {/* Colour swatch matching the canvas box */}
                <span style={{
                  width: "12px", height: "12px",
                  borderRadius: "3px",
                  background: det.color,
                  flexShrink: 0,
                }}/>

                <span style={{ flex: 1, fontWeight: 500, color: "#111827" }}>
                  {det.class_name.replace(/_/g, " ")}
                </span>

                {/* Confidence pill */}
                <span style={{
                  fontSize: "12px",
                  padding: "2px 8px",
                  borderRadius: "999px",
                  background: "#e0e7ff",
                  color: "#4338ca",
                  fontWeight: 500,
                }}>
                  {(det.confidence * 100).toFixed(1)}%
                </span>

                {/* Pixel coordinates */}
                <span style={{ fontSize: "12px", color: "#9ca3af", fontFamily: "monospace" }}>
                  [{det.bbox.x1}, {det.bbox.y1}]
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
