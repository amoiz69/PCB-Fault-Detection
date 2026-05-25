// frontend/src/api/client.js
// --------------------------
// All API calls live here. Components import these functions,
// never write fetch() directly. This means if the backend URL
// changes, you fix it in one place.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

/**
 * POST /api/inspect
 * Sends an image file and returns the detection result.
 *
 * @param {File} file - The image File object from the input/drop event
 * @returns {Promise<Object>} Detection result with bounding boxes
 */
export async function inspectImage(file) {
  const formData = new FormData();
  formData.append("file", file);      // "file" must match the FastAPI param name

  const res = await fetch(`${BASE_URL}/inspect`, {
    method: "POST",
    body: formData,
    // Do NOT set Content-Type header — browser sets it automatically
    // with the correct multipart boundary when using FormData
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

/**
 * GET /api/history
 * Returns the N most recent inspections.
 *
 * @param {number} limit - Max number of records to fetch
 */
export async function getHistory(limit = 50) {
  const res = await fetch(`${BASE_URL}/history?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch history: HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /api/stats
 * Returns aggregate statistics across all inspections.
 */
export async function getStats() {
  const res = await fetch(`${BASE_URL}/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats: HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /api/image/{id}
 * Returns the URL to serve the original uploaded image.
 * We don't fetch this — we just construct the URL for <img src="...">
 *
 * @param {number} inspectionId
 */
export function getImageUrl(inspectionId) {
  return `${BASE_URL}/image/${inspectionId}`;
}

/**
 * GET /api/report/{id}
 * Fetches the full structured JSON inspection report for a board.
 *
 * @param {number} inspectionId
 */
export async function getReport(inspectionId) {
  const res = await fetch(`${BASE_URL}/report/${inspectionId}`);
  if (!res.ok) throw new Error(`Failed to fetch report: HTTP ${res.status}`);
  return res.json();
}
