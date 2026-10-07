#!/usr/bin/env python3
"""
train_dog_on_roof.py

Train a SINGLE-CLASS YOLOv8 detector:
  class 0 = dog_on_roof

No car class. No roof geometry. The model learns the full concept
from your labeled images (see DATASET_GUIDE.md).

Usage:
  pip install -r requirements.txt
  python train_dog_on_roof.py
  python train_dog_on_roof.py --epochs 80 --model yolov8n.pt
"""

import argparse
from pathlib import Path
from typing import Tuple

from ultralytics import YOLO


def count_labeled(label_dir: Path) -> Tuple[int, int]:
    pos = neg = 0
    if not label_dir.exists():
        return 0, 0
    for p in label_dir.glob("*.txt"):
        text = p.read_text(encoding="utf-8").strip()
        if text:
            pos += 1
        else:
            neg += 1
    return pos, neg


def main():
    parser = argparse.ArgumentParser(description="Train dog_on_roof single-class detector")
    parser.add_argument("--data", default="data.yaml", help="YOLO data yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base weights (n/s/m)")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--name", default="dog_on_roof")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    data = root / args.data
    train_labels = root / "dataset" / "labels" / "train"
    val_labels = root / "dataset" / "labels" / "val"

    tr_pos, tr_neg = count_labeled(train_labels)
    va_pos, va_neg = count_labeled(val_labels)

    print("==================================================")
    print("  Train: DOG SITTING ON CAR ROOF (1 class)")
    print("==================================================")
    print(f"  data yaml     : {data}")
    print(f"  train +/−     : {tr_pos} positives / {tr_neg} negatives")
    print(f"  val   +/−     : {va_pos} positives / {va_neg} negatives")
    print("==================================================")

    if tr_pos < 20:
        print("[WARN] Very few positive labels. Read DATASET_GUIDE.md")
        print("       Aim for ≥150 labeled dog-on-roof images before production use.")

    # Prefer local yolov8n.pt from parent project if present
    model_path = args.model
    parent_pt = root.parent / "yolov8n.pt"
    if args.model == "yolov8n.pt" and parent_pt.exists():
        model_path = str(parent_pt)
        print(f"[INFO] Using existing weights: {model_path}")

    model = YOLO(model_path)
    results = model.train(
        data=str(data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        name=args.name,
        project=str(root / "runs" / "detect"),
        exist_ok=True,
        patience=20,
        # Augmentations help Indian street variability
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
    )

    best = root / "runs" / "detect" / args.name / "weights" / "best.pt"
    print("\n[DONE] Training finished.")
    print(f"  Best weights: {best}")
    print("  Run live:")
    print(f"    python detect_dog_on_roof.py --weights {best}")


if __name__ == "__main__":
    main()
