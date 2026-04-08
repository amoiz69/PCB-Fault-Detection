# PCB Defect Detection with YOLOv8

Automated optical inspection system for detecting PCB manufacturing defects using YOLOv8.

## Defect Classes

| ID | Class | Description |
|----|-------|-------------|
| 0 | `missing_hole` | Drill hole absent |
| 1 | `mouse_bite` | Small notch on PCB edge |
| 2 | `open_circuit` | Broken trace |
| 3 | `short` | Unintended trace connection |
| 4 | `spur` | Unwanted copper protrusion |
| 5 | `spurious_copper` | Extra copper in wrong location |

---

## Project Structure

```
pcb-defect-detection/
├── configs/
│   ├── dataset.yaml        # Dataset paths and class definitions
│   └── train_config.yaml   # All training hyperparameters
├── data/
│   ├── raw/                # Downloaded DeepPCB repo
│   ├── processed/          # Intermediate files
│   └── splits/             # Final train/val/test in YOLO format
│       ├── train/images/  train/labels/
│       ├── val/images/    val/labels/
│       └── test/images/   test/labels/
├── models/                 # Store exported models here
├── notebooks/
│   └── explore_dataset.ipynb
├── runs/                   # Training outputs (auto-generated)
├── scripts/
│   ├── prepare_dataset.py  # Download + convert DeepPCB → YOLO format
│   ├── train.py            # Training entry point
│   ├── evaluate.py         # Test-set evaluation + metrics
│   └── infer.py            # Run inference on new images
├── requirements.txt
└── README.md
```

---

## Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare dataset
```bash
python scripts/prepare_dataset.py
```
Downloads DeepPCB from GitHub (~150MB) and converts annotations to YOLO format.
Expected output: ~1,000+ labeled train images.

### 3. Explore the data (optional)
```bash
jupyter notebook notebooks/explore_dataset.ipynb
```

### 4. Train
```bash
# Default run (100 epochs, batch=16, YOLOv8s)
python scripts/train.py

# Quick smoke-test (5 epochs, small batch)
python scripts/train.py --epochs 5 --batch 8

# Resume interrupted training
python scripts/train.py --resume runs/pcb_defect_v1/weights/last.pt

# With WandB logging
python scripts/train.py --wandb
```

### 5. Evaluate
```bash
python scripts/evaluate.py --weights runs/pcb_defect_v1/weights/best.pt
```

### 6. Run inference
```bash
# On a single image
python scripts/infer.py \
    --weights runs/pcb_defect_v1/weights/best.pt \
    --source path/to/pcb_image.jpg

# On a directory of images
python scripts/infer.py \
    --weights runs/pcb_defect_v1/weights/best.pt \
    --source data/splits/test/images/
```

---

## Configuration

Edit `configs/train_config.yaml` to tune hyperparameters:

```yaml
model:  yolov8s.pt     # yolov8n (fast) | yolov8s | yolov8m (accurate)
epochs: 100
batch:  16
imgsz:  640
lr0:    0.001
device: 0              # GPU id or 'cpu'
```

---

## Target Metrics (Phase 1 Goal)

| Metric | Target |
|--------|--------|
| mAP@0.50 | > 0.80 |
| mAP@0.50:0.95 | > 0.55 |
| Inference speed | < 20ms/image (GPU) |

---

## Troubleshooting

**No GPU / CUDA errors:**
Set `device: cpu` in `train_config.yaml`. Training will be slower but works fine for this dataset size.

**Out of memory:**
Reduce `batch` to 8 or 4 in config.

**Low mAP on first run:**
PCB defects are small objects — ensure `mosaic: 1.0` and `imgsz: 640` are set. Try training longer (150 epochs).

**Dataset not found after cloning:**
Check that `data/raw/DeepPCB/PCBData/` exists and contains group folders. Re-run `prepare_dataset.py`.

---

## Next Steps (Phase 2)

- [ ] Build FastAPI backend wrapping the trained model
- [ ] React frontend with drag-and-drop upload and bbox overlay canvas
- [ ] Inspection history log with SQLite
- [ ] Reference board comparison (OpenCV homography)
