# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PCB Defect Inspector — a FastAPI backend + React (Vite) frontend wrapping a YOLOv8 model (`best.pt`) trained in Phase 1 to detect six PCB defect classes: `missing_hole`, `mouse_bite`, `open_circuit`, `short`, `spur`, `spurious_copper`.

## Running the Project

**Backend** (runs on port 8000):
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Swagger UI: `http://localhost:8000/docs`

**Frontend** (runs on port 5173):
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. Vite proxies `/api/*` → `http://localhost:8000` automatically — no env vars needed in dev.

**Diagnostic script** (for false-positive analysis):
```bash
cd backend
python ../scripts/diagnose.py --source path/to/pcb_images/ --weights models/best.pt
```

## Architecture

### Request flow
```
Browser → POST /api/inspect (FormData)
→ FastAPI saves image to backend/uploads/ (UUID filename)
→ run_inference() calls YOLOv8 model singleton
→ score_detections() enriches each bbox with severity, adds board grade
→ result saved to SQLite (backend/inspections.db)
→ JSON returned to React, DetectionCanvas draws scaled bboxes
```

### Backend (`backend/`)

- **`main.py`** — FastAPI app. Uses lifespan context manager to call `load_model()` and `create_tables()` exactly once at startup.
- **`routers/inspect.py`** — All API routes: `POST /inspect`, `GET /history`, `GET /stats`, `GET /image/{id}`, `GET /report/{id}`.
- **`services/inference.py`** — YOLO model singleton (`_model` global). `load_model()` loads `best.pt` once; `run_inference()` calls it per request. Calls `score_detections()` before returning.
- **`services/severity.py`** — Stateless scoring. `score_detections()` mutates detection dicts in-place, adding `severity`, `severity_color`, `severity_score`, `area_pct`. Returns board-level `quality_score` (0–100), `grade` (A–F), `severity_summary`, and `recommendation`.
- **`models/database.py`** — SQLAlchemy `Inspection` table + `create_tables()`. Includes lightweight `ALTER TABLE` migrations for columns added post-initial-release (severity fields); safe to run on every startup.

### Frontend (`frontend/src/`)

- **`App.jsx`** — Single source of truth for all state (`result`, `imageUrl`, `history`, `stats`, `loading`, `error`, `selectedId`). Owns upload and history-selection handlers.
- **`api/client.js`** — All `fetch()` calls centralized here. `BASE_URL` defaults to `/api` (proxied by Vite). Never set `Content-Type` when sending `FormData` — the browser sets the multipart boundary automatically.
- **`components/DetectionCanvas.jsx`** — Draws image on `<canvas>` and overlays bboxes. Bboxes from the model are pixel coordinates for the original image size; scale factor `displayWidth / imageWidth` must be applied. `image_width`/`image_height` come from the API response (history items default to 640×640).
- **`components/SeverityReport.jsx`** — Displays the per-defect severity breakdown and board grade from the `severity_summary` / `grade` / `quality_score` fields.

## Key Invariants

- **Model is a singleton** — never load `YOLO(weights)` per-request; it takes ~1–2s. Always go through `run_inference()`.
- **DB migrations run on every startup** — `_migrate_add_severity_columns()` checks column existence before `ALTER TABLE`; adding new columns to `Inspection` requires a matching migration entry there.
- **Uploads are UUID-named** — prevents filename collisions; the original filename is stored in `Inspection.filename` for display only.
- **`score_detections()` mutates in-place** — detection dicts are enriched before being JSON-serialized to the DB; don't re-run scoring on data loaded from DB.
