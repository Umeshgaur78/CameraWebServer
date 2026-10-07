#!/usr/bin/env python3
"""
validate_dataset.py — Quick check before training.

Usage:
  python validate_dataset.py
"""

from pathlib import Path


def main():
    root = Path(__file__).resolve().parent / "dataset"
    issues = 0

    for split in ("train", "val"):
        img_dir = root / "images" / split
        lbl_dir = root / "labels" / split
        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpeg"))
        print(f"\n[{split}] images={len(images)}")

        pos = neg = missing = bad = 0
        for img in images:
            lbl = lbl_dir / (img.stem + ".txt")
            if not lbl.exists():
                missing += 1
                issues += 1
                print(f"  MISSING label: {lbl.name}")
                continue
            lines = [ln.strip() for ln in lbl.read_text(encoding="utf-8").splitlines() if ln.strip()]
            if not lines:
                neg += 1
                continue
            pos += 1
            for ln in lines:
                parts = ln.split()
                if len(parts) != 5:
                    bad += 1
                    issues += 1
                    print(f"  BAD line in {lbl.name}: {ln}")
                    continue
                cls = int(float(parts[0]))
                vals = list(map(float, parts[1:]))
                if cls != 0:
                    bad += 1
                    issues += 1
                    print(f"  BAD class id {cls} in {lbl.name} (must be 0=dog_on_roof)")
                if any(v < 0 or v > 1 for v in vals):
                    bad += 1
                    issues += 1
                    print(f"  BAD normalized coords in {lbl.name}: {vals}")

        print(f"  positives(dog_on_roof)={pos}  negatives={neg}  missing_labels={missing}  bad={bad}")

    print("\n[RESULT]", "OK — ready to train" if issues == 0 else f"{issues} issue(s) — fix before training")


if __name__ == "__main__":
    main()
