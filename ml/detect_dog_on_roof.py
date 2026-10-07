#!/usr/bin/env python3
"""
detect_dog_on_roof.py

Uses COCO YOLOv8 class "dog" (same fixed pipeline as ../detect_dog_on_car.py).
Car/roof are background. Relay ON only when a dog is detected.

Custom dog_on_roof weights are optional later; default is yolov8n.pt + class dog.

Usage:
  python detect_dog_on_roof.py --esp32 172.20.10.9 --conf 0.25
  python detect_dog_on_roof.py --image ../test.jpg --conf 0.20
"""

import runpy
from pathlib import Path

# Reuse the fixed root detector (single source of truth)
root_script = Path(__file__).resolve().parent.parent / "detect_dog_on_car.py"
runpy.run_path(str(root_script), run_name="__main__")
