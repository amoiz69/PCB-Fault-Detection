"""
scripts/train.py
----------------
Trains YOLOv8 on the prepared PCB defect dataset.

Usage:
    # Basic run
    python scripts/train.py

    # Override epochs and batch size
    python scripts/train.py --epochs 50 --batch 8
    # Use a specific device
    python scripts/train.py --device mps

    # Enable WandB logging
    python scripts/train.py --wandb
"""

import argparse
import os
from pathlib import Path
import torch

import yaml
from ultralytics import YOLO

def resolve_device(requested_device):
    mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    cuda_available = torch.cuda.is_available()

    if requested_device is None:
        if mps_available:
            return "mps"
        if cuda_available:
            return 0
        return "cpu"

    device = str(requested_device).strip().lower()
    is_cuda_request = device.isdigit() or (
        "," in device and all(part.strip().isdigit() for part in device.split(","))
    )

    if device == "mps" and not mps_available:
        fallback = 0 if cuda_available else "cpu"
        print(f"[WARN] MPS requested but not available. Falling back to {fallback}.")
        return fallback

    if is_cuda_request and not cuda_available:
        fallback = "mps" if mps_available else "cpu"
        print(f"[WARN] CUDA requested (device={requested_device}) but not available. Falling back to {fallback}.")
        return fallback

    return requested_device


def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLOv8 for PCB defect detection")
    parser.add_argument("--config",   default="configs/train_config.yaml", help="Path to train config")
    parser.add_argument("--epochs",   type=int,   default=None, help="Override epochs")
    parser.add_argument("--batch",    type=int,   default=None, help="Override batch size")
    parser.add_argument("--imgsz",    type=int,   default=None, help="Override image size")
    parser.add_argument("--device",   default=None, help="Device: 0, 1, mps, cpu")
    parser.add_argument("--resume",   default=None, help="Path to checkpoint to resume from")
    parser.add_argument("--wandb",    action="store_true", help="Enable WandB logging")
    return parser.parse_args()


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    args = parse_args()

    # ── WandB (optional) ──────────────────────────────────────────────────────
    if args.wandb:
        try:
            import wandb
            wandb.init(project="pcb-defect-detection", name="yolov8s-baseline")
            print("[INFO] WandB logging enabled.")
        except ImportError:
            print("[WARN] wandb not installed. Run: pip install wandb")

    # ── Load config ───────────────────────────────────────────────────────────
    cfg = load_config(args.config)

    # CLI overrides
    if args.epochs  is not None: cfg["epochs"]  = args.epochs
    if args.batch   is not None: cfg["batch"]   = args.batch
    if args.imgsz   is not None: cfg["imgsz"]   = args.imgsz
    cfg["device"] = resolve_device(args.device if args.device is not None else cfg.get("device"))

    model_weights = args.resume if args.resume else cfg.pop("model", "yolov8s.pt")
    data_cfg      = cfg.pop("data", "configs/dataset.yaml")

    print(f"[INFO] Model  : {model_weights}")
    print(f"[INFO] Data   : {data_cfg}")
    print(f"[INFO] Epochs : {cfg['epochs']}")
    print(f"[INFO] Batch  : {cfg['batch']}")
    print(f"[INFO] Device : {cfg.get('device', 'auto')}")

    # ── Train ─────────────────────────────────────────────────────────────────
    model = YOLO(model_weights)

    results = model.train(
        data=data_cfg,
        **cfg,
    )

    print("\n[DONE] Training complete.")
    print(f"       Best weights : {results.save_dir}/weights/best.pt")
    print(f"       Last weights : {results.save_dir}/weights/last.pt")
    print(f"       Results dir  : {results.save_dir}")


if __name__ == "__main__":
    main()
