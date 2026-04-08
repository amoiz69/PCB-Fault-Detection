# PCB Defect Inspector — Phase 2 (Web App)

FastAPI backend + React frontend wrapping the Phase 1 YOLOv8 model.

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- `best.pt` from Phase 1 training placed at `models/best.pt`

---

## Project Structure

```
pcb-phase2/
├── backend/
│   ├── main.py                  ← FastAPI app entry point
│   ├── requirements.txt
│   ├── models/
│   │   └── database.py          ← SQLAlchemy + Inspection table
│   ├── routers/
│   │   └── inspect.py           ← /inspect, /history, /stats, /image endpoints
│   └── services/
│       └── inference.py         ← YOLOv8 model singleton + run_inference()
├── frontend/
│   └── src/
│       ├── App.jsx              ← Root component, owns all state
│       ├── api/
│       │   └── client.js        ← All fetch() calls in one place
│       └── components/
│           ├── UploadZone.jsx   ← Drag-and-drop image upload
│           ├── DetectionCanvas.jsx ← Canvas bbox overlay
│           ├── DefectSummary.jsx   ← Pass/fail verdict + defect list
│           ├── HistoryPanel.jsx    ← Inspection history sidebar
│           └── StatsBar.jsx        ← Aggregate stats at the top
└── models/
    └── best.pt                  ← Your trained weights from Phase 1
```

---

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/inspect` | Upload image → run inference → return detections |
| GET | `/api/history` | List past inspections (newest first) |
| GET | `/api/stats` | Aggregate stats (pass rate, defect breakdown) |
| GET | `/api/image/{id}` | Serve the original uploaded image |

---

## Running the Frontend

```bash
cd frontend

# First time: initialise a Vite + React project here
npm create vite@latest . -- --template react
# When asked: select "React" and "JavaScript"

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open `http://localhost:5173`.

---

## How It Works End-to-End

```
1. User drops a PCB image onto the upload zone
2. React calls POST /api/inspect with the image as FormData
3. FastAPI saves the image to /uploads/, runs YOLOv8 inference
4. Detections (class, confidence, pixel bbox) returned as JSON
5. React draws the image on a <canvas> and overlays coloured boxes
6. Result saved to SQLite — appears in history sidebar immediately
7. Clicking a history item reloads its image + detections into the canvas
```

---

## Key Code Concepts

### Model singleton (inference.py)
The YOLO model is loaded once at startup and reused for every request.
Loading takes ~1-2s; inference takes ~50ms. Never load it per-request.

### Canvas scaling (DetectionCanvas.jsx)
The model outputs pixel coordinates for a 640×640 image.
The canvas is displayed smaller on screen.
Scale factor = `displayWidth / modelImageWidth` is applied to every bbox coordinate.

### FormData upload (client.js)
Never set `Content-Type` manually when using FormData.
The browser sets it automatically with the correct multipart boundary.

---

## Phase 3 Extensions (future)

- Reference board comparison (OpenCV homography)
- Anomaly detection mode (PatchCore)
- Batch processing queue (Celery + Redis)
- Edge deployment export (ONNX → TFLite → Raspberry Pi)
