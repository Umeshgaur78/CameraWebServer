"""Inject Help button + problem photo modal into index_dog.h only."""
from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image

INDEX = Path(r"c:\Users\umesh\OneDrive\Documents\Arduino\CameraWebServer\index_dog.h")
ASSETS = Path(
    r"C:\Users\umesh\.cursor\projects\c-Users-umesh-OneDrive-Documents-Arduino-CameraWebServer\assets"
)

# User-provided problem photos (order for gallery)
KEYS = [
    ("shutterstock_2647075239", "Dogs sitting on car roof / trunk"),
    ("bear-scratches", "Claw scratches on car paint / hood"),
    ("R-7b25cb39", "Stray dog resting on car roof"),
    ("DSC03847", "Roof paint scratched by animal claws"),
    ("IMG_44472", "Roof dent from heavy weight on top"),
    ("b10b4da0", "Two dogs lying on car roof"),
    ("street-dog", "Dog sleeping on car roof"),
]


def find_file(key: str) -> Path:
    for f in ASSETS.glob("*.png"):
        if key.lower() in f.name.lower():
            return f
    raise FileNotFoundError(key)


def to_data_url(path: Path) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((400, 280))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=40, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return "data:image/jpeg;base64," + b64


def main():
    imgs = []
    for key, cap in KEYS:
        url = to_data_url(find_file(key))
        imgs.append((cap, url))
        print(key, "ok", len(url))

    css = """
    .help-btn {
      margin-top: 8px;
      width: 100%;
      border: 1px solid rgba(56,189,248,0.45);
      background: rgba(56,189,248,0.12);
      color: #e2e8f0;
      border-radius: 8px;
      padding: 10px 12px;
      font: 600 13px Space Grotesk, sans-serif;
      cursor: pointer;
    }
    .help-btn:hover { background: rgba(56,189,248,0.22); }
    .help-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: rgba(2,6,12,0.82);
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .help-overlay.open { display: flex; }
    .help-modal {
      width: min(720px, 100%);
      max-height: 90vh;
      overflow: auto;
      background: #0f1720;
      border: 1px solid rgba(148,163,184,0.25);
      border-radius: 12px;
      padding: 16px 16px 20px;
      color: #e2e8f0;
      box-shadow: 0 20px 50px rgba(0,0,0,0.45);
    }
    .help-modal h2 {
      margin: 0 0 8px;
      font: 700 18px Space Grotesk, sans-serif;
      color: #f8fafc;
    }
    .help-modal p {
      margin: 0 0 10px;
      font: 400 13px/1.45 Space Grotesk, sans-serif;
      color: #cbd5e1;
    }
    .help-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }
    .help-card {
      background: #111827;
      border: 1px solid rgba(148,163,184,0.18);
      border-radius: 8px;
      overflow: hidden;
    }
    .help-card img {
      display: block;
      width: 100%;
      height: 140px;
      object-fit: cover;
      background: #020617;
    }
    .help-card span {
      display: block;
      padding: 8px;
      font: 500 11px/1.35 Space Grotesk, sans-serif;
      color: #94a3b8;
    }
    .help-close {
      margin-top: 14px;
      width: 100%;
      border: 0;
      border-radius: 8px;
      padding: 10px;
      background: #38bdf8;
      color: #0b1220;
      font: 700 13px Space Grotesk, sans-serif;
      cursor: pointer;
    }
"""

    cards = []
    for cap, url in imgs:
        cards.append(
            f'<div class="help-card"><img src="{url}" alt="{cap}"><span>{cap}</span></div>'
        )
    cards_html = "\n".join(cards)

    modal = f"""
  <div class="help-overlay" id="helpOverlay" aria-hidden="true">
    <div class="help-modal" role="dialog" aria-labelledby="helpTitle">
      <h2 id="helpTitle">Why this project?</h2>
      <p>Humne ye project is problem ki wajah se banaya hai: stray dogs gadi ke <b>roof</b> par baithte / soote hain.</p>
      <p>Isse car ke roof par <b>damage</b> hota hai, paint par <b>scratches / claw marks</b> padte hain, aur kabhi-kabhi <b>glass / windshield</b> bhi kharab ho sakta hai.</p>
      <p>Isliye ESP32-CAM se dog detect karke alert (relay/flash) diya jata hai — taaki gadi safe rahe.</p>
      <div class="help-grid">
{cards_html}
      </div>
      <button type="button" class="help-close" id="helpCloseBtn">Close</button>
    </div>
  </div>
"""

    btn = """        <button type="button" class="help-btn" id="helpBtn">Help — Why this project?</button>
"""

    js = """
    const helpBtn = document.getElementById('helpBtn');
    const helpOverlay = document.getElementById('helpOverlay');
    const helpCloseBtn = document.getElementById('helpCloseBtn');
    if (helpBtn && helpOverlay) {
      helpBtn.onclick = function () {
        helpOverlay.classList.add('open');
        helpOverlay.setAttribute('aria-hidden', 'false');
      };
      function closeHelp() {
        helpOverlay.classList.remove('open');
        helpOverlay.setAttribute('aria-hidden', 'true');
      }
      if (helpCloseBtn) helpCloseBtn.onclick = closeHelp;
      helpOverlay.addEventListener('click', function (e) {
        if (e.target === helpOverlay) closeHelp();
      });
    }
"""

    text = INDEX.read_text(encoding="utf-8")

    if "help-overlay" in text or 'id="helpBtn"' in text:
        # remove previous help injection blocks if re-run
        text = re.sub(r"\n    /\* HELP_UI_START \*/.*?/\* HELP_UI_END \*/\n", "\n", text, flags=re.S)
        text = re.sub(r"\n  /\* HELP_MODAL_START \*/.*?/\* HELP_MODAL_END \*/\n", "\n", text, flags=re.S)
        text = re.sub(
            r"\n        <button type=\"button\" class=\"help-btn\" id=\"helpBtn\">.*?</button>\n",
            "\n",
            text,
        )
        text = re.sub(r"\n    /\* HELP_JS_START \*/.*?/\* HELP_JS_END \*/\n", "\n", text, flags=re.S)

    if "  </style>" not in text:
        raise SystemExit("style end not found")
    text = text.replace(
        "  </style>",
        "    /* HELP_UI_START */\n" + css + "    /* HELP_UI_END */\n  </style>",
        1,
    )

    marker_btn = '        <button type="button" class="zone-btn" id="clearZoneBtn">Clear Detect Zone</button>\n'
    if marker_btn not in text:
        raise SystemExit("clear zone btn not found")
    text = text.replace(marker_btn, marker_btn + btn, 1)

    marker_script = '  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>'
    if marker_script not in text:
        raise SystemExit("tf script not found")
    text = text.replace(
        marker_script,
        "  /* HELP_MODAL_START */\n" + modal + "  /* HELP_MODAL_END */\n" + marker_script,
        1,
    )

    # Insert JS after clearZoneBtn handler block ends — after setRelay(false) is fine, before boot
    marker_js = "    setRelay(false);"
    if marker_js not in text:
        raise SystemExit("setRelay marker not found")
    text = text.replace(
        marker_js,
        "    /* HELP_JS_START */\n" + js + "    /* HELP_JS_END */\n" + marker_js,
        1,
    )

    INDEX.write_text(text, encoding="utf-8")
    print("Updated", INDEX)
    print("Sketch will grow by ~", sum(len(u) for _, u in imgs), "chars of image data")


if __name__ == "__main__":
    main()
