#!/usr/bin/env python3
"""Quick test: Send a real dog image to Railway server to verify detection works"""
import requests

SERVER = "https://esp32-dog-detector-production.up.railway.app"
SECRET = "YOUR_ALERT_SECRET"

# 1. Check server is online
print("[TEST] Checking server...")
r = requests.get(SERVER)
print(f"  Status: {r.json()}")

# 2. Download a clear dog image from internet
print("[TEST] Downloading dog image...")
dog_urls = [
    "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=640",
    "https://cdn.pixabay.com/photo/2016/12/13/05/15/puppy-1903313_640.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/320px-YellowLabradorLooking_new.jpg",
]

img_data = None
for url in dog_urls:
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and len(resp.content) > 1000:
            img_data = resp.content
            print(f"  Downloaded: {len(img_data)} bytes from {url[:50]}...")
            break
    except:
        continue

if not img_data:
    # Use a local test - create a simple test with existing yolov8n model
    print("  Could not download. Testing with local file...")
    import os
    # Check if any jpg exists
    for f in os.listdir("."):
        if f.endswith(".jpg") and os.path.getsize(f) > 1000:
            with open(f, "rb") as fh:
                img_data = fh.read()
            print(f"  Using local file: {f} ({len(img_data)} bytes)")
            break

if not img_data:
    print("  ERROR: No test image available")
    exit(1)

# 3. Send to /detect endpoint
print("[TEST] Sending image to server for detection...")
r = requests.post(
    f"{SERVER}/detect",
    data=img_data,
    headers={
        "Content-Type": "image/jpeg",
        "x-alert-secret": SECRET
    },
    timeout=60
)
print(f"  HTTP Status: {r.status_code}")
print(f"  Response: {r.text}")

try:
    data = r.json()
    if data.get("dog"):
        print("\n✅ SUCCESS! Server detected the dog correctly!")
        print(f"   Score: {data.get('score')}")
        print(f"   Seen: {data.get('seen')}")
    else:
        print(f"\n❌ Dog NOT detected. Seen objects: {data.get('seen', [])}")
except:
    print(f"\n  Raw response: {r.text[:200]}")
