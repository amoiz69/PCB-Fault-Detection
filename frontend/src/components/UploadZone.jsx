// frontend/src/components/UploadZone.jsx
// ---------------------------------------
// Drag-and-drop upload zone.
// The user can drag a PCB image onto it or click to browse.
// On drop/select it calls onUpload(file) with the File object.

import { useState, useRef } from "react";

export default function UploadZone({ onUpload, loading }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  // Prevent browser from navigating to the dropped file
  const prevent = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    prevent(e);
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onUpload(file);
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    e.target.value = "";   // reset so the same file can be uploaded again
  };

  return (
    <div
      onDragOver={(e) => { prevent(e); setDragging(true); }}
      onDragLeave={(e) => { prevent(e); setDragging(false); }}
      onDrop={handleDrop}
      onClick={() => !loading && inputRef.current?.click()}
      style={{
        border: `2px dashed ${dragging ? "#6366f1" : "#d1d5db"}`,
        borderRadius: "12px",
        padding: "48px 24px",
        textAlign: "center",
        cursor: loading ? "not-allowed" : "pointer",
        background: dragging ? "#eef2ff" : "#f9fafb",
        transition: "border-color 0.2s, background 0.2s",
        userSelect: "none",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        style={{ display: "none" }}
      />

      {/* Upload icon (simple SVG — no external dependency) */}
      <svg
        width="40" height="40" viewBox="0 0 24 24" fill="none"
        stroke={dragging ? "#6366f1" : "#9ca3af"}
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        style={{ margin: "0 auto 12px", display: "block" }}
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>

      {loading ? (
        <p style={{ color: "#6b7280", margin: 0 }}>Inspecting…</p>
      ) : (
        <>
          <p style={{ color: "#111827", fontWeight: 500, margin: "0 0 4px" }}>
            Drop a PCB image here
          </p>
          <p style={{ color: "#6b7280", fontSize: "14px", margin: 0 }}>
            or click to browse — JPG, PNG, BMP supported
          </p>
        </>
      )}
    </div>
  );
}
