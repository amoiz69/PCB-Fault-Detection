// frontend/src/App.jsx
// ---------------------
// Root component. Owns all state and wires the child components together.
//
// State:
//   result      — the latest inference result (or a historical one if selected)
//   imageUrl    — URL of the image to show on the canvas
//   history     — list of past inspections from /api/history
//   stats       — aggregate stats from /api/stats
//   loading     — true while a request is in-flight
//   error       — error message string if something went wrong
//   selectedId  — which history item is highlighted in the sidebar

import { useState, useEffect, useCallback } from "react";
import { inspectImage, getHistory, getStats, getImageUrl } from "./api/client";
import UploadZone    from "./components/UploadZone";
import DetectionCanvas from "./components/DetectionCanvas";
import DefectSummary from "./components/DefectSummary";
import SeverityReport from "./components/SeverityReport";
import HistoryPanel  from "./components/HistoryPanel";
import StatsBar      from "./components/StatsBar";

export default function App() {
  const [result,     setResult]     = useState(null);
  const [imageUrl,   setImageUrl]   = useState(null);
  const [history,    setHistory]    = useState([]);
  const [stats,      setStats]      = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  // Fetch history and stats — called at mount and after each new inspection
  const refreshData = useCallback(async () => {
    try {
      const [h, s] = await Promise.all([getHistory(), getStats()]);
      setHistory(h);
      setStats(s);
    } catch (e) {
      console.error("Failed to refresh data:", e);
    }
  }, []);

  useEffect(() => { refreshData(); }, [refreshData]);

  // Called when user drops/selects a file
  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);

    // Show a local preview immediately (before the server responds)
    const localUrl = URL.createObjectURL(file);
    setImageUrl(localUrl);
    setResult(null);
    setSelectedId(null);

    try {
      const data = await inspectImage(file);
      setResult(data);
      setSelectedId(data.id);
      // Replace the local blob URL with the server URL
      setImageUrl(getImageUrl(data.id));
      await refreshData();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Called when user clicks a history item
  const handleSelectHistory = (item) => {
    setSelectedId(item.id);
    setImageUrl(getImageUrl(item.id));
    // Reconstruct the result shape from the history item
    setResult({
      id:              item.id,
      filename:        item.filename,
      passed:          item.passed,
      defect_count:    item.defect_count,
      confidence_avg:  item.confidence_avg,
      detections:      item.detections,
      // History items don't store image dimensions — default to 640×640
      image_width:     640,
      image_height:    640,
      // Severity fields
      quality_score:    item.quality_score,
      grade:            item.grade,
      severity_summary: item.severity_summary,
      recommendation:   null,   // not stored in history; report endpoint has it
    });
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#f3f4f6",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      {/* Header */}
      <header style={{
        background: "white",
        borderBottom: "1px solid #e5e7eb",
        padding: "0 24px",
        height: "56px",
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
          stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="2" width="20" height="20" rx="2"/>
          <circle cx="12" cy="12" r="3"/>
          <path d="M2 9h2M2 15h2M20 9h2M20 15h2M9 2v2M15 2v2M9 20v2M15 20v2"/>
        </svg>
        <span style={{ fontWeight: 600, fontSize: "16px", color: "#111827" }}>
          PCB Defect Inspector
        </span>
        <span style={{ fontSize: "13px", color: "#9ca3af", marginLeft: "4px" }}>
          Phase 2
        </span>
      </header>

      {/* Main layout: left panel + right sidebar */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 320px",
        gap: "20px",
        padding: "20px 24px",
        maxWidth: "1200px",
        margin: "0 auto",
      }}>

        {/* LEFT PANEL */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

          {/* Stats bar */}
          <StatsBar stats={stats} />

          {/* Upload zone */}
          <div style={{
            background: "white",
            borderRadius: "12px",
            padding: "20px",
            border: "1px solid #e5e7eb",
          }}>
            <UploadZone onUpload={handleUpload} loading={loading} />

            {error && (
              <div style={{
                marginTop: "12px",
                padding: "10px 14px",
                borderRadius: "8px",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
                fontSize: "14px",
              }}>
                {error}
              </div>
            )}
          </div>

          {/* Canvas + defect summary */}
          {imageUrl && (
            <div style={{
              background: "white",
              borderRadius: "12px",
              padding: "20px",
              border: "1px solid #e5e7eb",
            }}>
              <DetectionCanvas
                imageUrl={imageUrl}
                detections={result?.detections || []}
                imageWidth={result?.image_width || 640}
                imageHeight={result?.image_height || 640}
              />
              <DefectSummary result={result} />
              <SeverityReport result={result} />
            </div>
          )}
        </div>

        {/* RIGHT SIDEBAR — history */}
        <div style={{
          background: "white",
          borderRadius: "12px",
          border: "1px solid #e5e7eb",
          overflow: "hidden",
          alignSelf: "start",
          maxHeight: "calc(100vh - 96px)",
          display: "flex",
          flexDirection: "column",
        }}>
          <div style={{
            padding: "14px 16px",
            borderBottom: "1px solid #e5e7eb",
            fontWeight: 500,
            fontSize: "14px",
            color: "#374151",
          }}>
            Inspection history
          </div>
          <div style={{ overflowY: "auto", flex: 1 }}>
            <HistoryPanel
              history={history}
              onSelect={handleSelectHistory}
              selectedId={selectedId}
            />
          </div>
        </div>

      </div>
    </div>
  );
}
