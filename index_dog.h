/**
 * index_dog.h
 *
 * ESP32-CAM — SIRF DOG detection
 * ==============================
 * UI only restyled — detection / relay logic unchanged.
 */

#ifndef INDEX_DOG_H
#define INDEX_DOG_H

const char INDEX_DOG_HTML[] = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESP32-CAM Dog Detection</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg0: #070a0e;
      --bg1: #0d131a;
      --panel: rgba(16, 22, 30, 0.88);
      --text: #e8eef6;
      --muted: #8a96a8;
      --ok: #3ddc84;
      --bad: #ff4d4d;
      --line: rgba(255,255,255,0.08);
      --glow-ok: rgba(61, 220, 132, 0.35);
      --glow-bad: rgba(255, 77, 77, 0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { min-height: 100%; }
    body {
      font-family: "Space Grotesk", sans-serif;
      color: var(--text);
      background:
        radial-gradient(1200px 600px at 10% -10%, rgba(61,220,132,0.07), transparent 55%),
        radial-gradient(900px 500px at 100% 0%, rgba(255,77,77,0.06), transparent 50%),
        linear-gradient(180deg, var(--bg1), var(--bg0));
      padding: 20px clamp(16px, 3vw, 28px) 28px;
    }
    .shell { max-width: 1100px; margin: 0 auto; }
    .project-footer {
      margin-top: 18px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
      text-align: center;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.72rem;
      color: var(--muted);
      letter-spacing: 0.02em;
      line-height: 1.5;
    }

    /* Top bar */
    .top {
      display: flex; align-items: center; justify-content: space-between;
      gap: 16px; margin-bottom: 16px; flex-wrap: wrap;
    }
    .brand {
      display: flex; align-items: center; gap: 14px;
    }
    .prohibit-mark {
      width: 52px; height: 52px; flex-shrink: 0;
      border-radius: 50%;
      border: 3.5px solid var(--bad);
      background: rgba(0,0,0,0.45);
      position: relative;
      display: grid; place-items: center;
      box-shadow: 0 0 0 4px rgba(255,77,77,0.12);
    }
    .prohibit-mark svg { width: 28px; height: 28px; fill: var(--text); opacity: 0.95; }
    .prohibit-mark::after {
      content: "";
      position: absolute; left: 50%; top: 50%;
      width: 118%; height: 3.5px;
      background: var(--bad);
      transform: translate(-50%, -50%) rotate(-45deg);
      border-radius: 2px;
      box-shadow: 0 0 8px rgba(255,77,77,0.5);
    }
    .brand-text { display: flex; flex-direction: column; gap: 2px; }
    .brand h1 {
      font-size: clamp(1.25rem, 2.2vw, 1.6rem);
      font-weight: 700; letter-spacing: -0.03em; line-height: 1.1;
    }
    .brand .tag {
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.72rem; color: var(--muted); letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .live-pill {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 12px; border-radius: 999px;
      background: rgba(0,0,0,0.35);
      border: 1px solid var(--line);
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.75rem; font-weight: 500; color: var(--muted);
    }
    .live-pill .dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: #555; box-shadow: none;
    }
    body.is-live .live-pill { color: var(--ok); border-color: rgba(61,220,132,0.35); }
    body.is-live .live-pill .dot {
      background: var(--ok);
      box-shadow: 0 0 0 0 var(--glow-ok);
      animation: pulse 1.6s ease-out infinite;
    }
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 var(--glow-ok); }
      70% { box-shadow: 0 0 0 10px transparent; }
      100% { box-shadow: 0 0 0 0 transparent; }
    }

    /* Layout — camera column narrower */
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 720px) 280px;
      gap: 20px; align-items: start;
      justify-content: center;
    }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; max-width: 520px; margin: 0 auto; }
    }

    .stage { display: flex; flex-direction: column; gap: 10px; max-width: 720px; }

    .zone-banner {
      display: flex; align-items: center; justify-content: center; gap: 10px;
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px dashed rgba(255,77,77,0.45);
      background: rgba(255,77,77,0.08);
      color: #ffb4b4;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.78rem; font-weight: 500;
      letter-spacing: 0.06em; text-transform: uppercase;
    }
    .zone-banner strong { color: var(--bad); font-weight: 700; }

    /* Camera stage — smaller */
    .viewer {
      position: relative;
      width: 100%;
      max-width: 680px;
      margin: 0 auto;
      background: #000;
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
      line-height: 0;
      box-shadow:
        0 0 0 1px rgba(255,255,255,0.03) inset,
        0 20px 50px rgba(0,0,0,0.45);
    }
    body.relay-on .viewer {
      box-shadow:
        0 0 0 1px rgba(255,77,77,0.45),
        0 0 36px rgba(255,77,77,0.18),
        0 20px 50px rgba(0,0,0,0.45);
    }
    #stream { display: block; width: 100%; height: auto; max-width: 100%; }
    #canvas {
      position: absolute; left: 0; top: 0; width: 100%; height: 100%;
      pointer-events: auto; cursor: crosshair; z-index: 4;
    }
    .hud-corner {
      position: absolute; z-index: 2; width: 16px; height: 16px;
      border-color: rgba(232,238,246,0.35); border-style: solid; pointer-events: none;
    }
    .hud-corner.tl { top: 10px; left: 10px; border-width: 2px 0 0 2px; }
    .hud-corner.tr { top: 10px; right: 10px; border-width: 2px 2px 0 0; }
    .hud-corner.bl { bottom: 10px; left: 10px; border-width: 0 0 2px 2px; }
    .hud-corner.br { bottom: 10px; right: 10px; border-width: 0 2px 2px 0; }

    /* Prohibited overlay — only when dog/relay active (CSS only) */
    .alert-overlay {
      position: absolute; z-index: 3; inset: 0;
      display: flex; flex-direction: column; align-items: center; justify-content: flex-start;
      padding-top: 14px;
      pointer-events: none;
      opacity: 0; transition: opacity 0.25s ease;
      background: linear-gradient(180deg, rgba(80,0,0,0.45) 0%, transparent 42%);
    }
    body.relay-on .alert-overlay { opacity: 1; }
    .alert-badge {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 14px 8px 10px;
      border-radius: 999px;
      background: rgba(20,0,0,0.82);
      border: 2px solid var(--bad);
      color: #fff;
      font-weight: 700; font-size: 0.85rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      animation: badgePop 0.9s ease-in-out infinite;
    }
    .alert-badge .mini-prohibit {
      width: 28px; height: 28px; border-radius: 50%;
      border: 2.5px solid var(--bad);
      display: grid; place-items: center;
      position: relative; flex-shrink: 0;
    }
    .alert-badge .mini-prohibit svg { width: 14px; height: 14px; fill: #fff; }
    .alert-badge .mini-prohibit::after {
      content: ""; position: absolute; left: 50%; top: 50%;
      width: 120%; height: 2.5px; background: var(--bad);
      transform: translate(-50%, -50%) rotate(-45deg);
    }
    @keyframes badgePop {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.04); }
    }

    /* Side panel */
    .panel {
      background: var(--panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 18px 16px 16px;
      display: flex; flex-direction: column; gap: 2px;
    }
    .panel-title {
      font-size: 0.72rem; font-family: "IBM Plex Mono", monospace;
      letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted);
      margin-bottom: 10px;
    }
    .row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 11px 0; border-bottom: 1px solid var(--line); font-size: 0.92rem;
    }
    .row:last-of-type { border-bottom: none; }
    .label { color: var(--muted); font-weight: 500; }
    .value {
      font-family: "IBM Plex Mono", monospace;
      font-weight: 500; font-size: 0.86rem;
    }
    .ok { color: var(--ok); }
    .bad { color: var(--bad); }

    .status-box {
      margin-top: 14px; padding: 14px 12px; border-radius: 10px;
      text-align: center; font-weight: 700; font-size: 0.95rem;
      letter-spacing: -0.01em; transition: background 0.25s, border-color 0.25s, color 0.25s;
    }
    .status-box.on {
      background: rgba(255, 77, 77, 0.12);
      color: var(--bad);
      border: 1px solid rgba(255, 77, 77, 0.4);
      animation: alertPulse 1.8s ease-in-out infinite;
    }
    .status-box.off {
      background: rgba(61, 220, 132, 0.08);
      color: var(--ok);
      border: 1px solid rgba(61, 220, 132, 0.28);
      animation: none;
    }
    @keyframes alertPulse {
      0%, 100% { box-shadow: 0 0 0 0 transparent; }
      50% { box-shadow: 0 0 22px var(--glow-bad); }
    }
    .hint {
      margin-top: 12px; color: var(--muted); font-size: 0.78rem; line-height: 1.45;
      opacity: 0.9;
    }
    .flash-btn {
      margin-top: 12px; width: 100%; padding: 11px 12px;
      border-radius: 10px; border: 1px solid var(--line);
      background: rgba(255,255,255,0.04); color: var(--text);
      font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 0.9rem;
      cursor: pointer;
    }
    .flash-btn.on {
      background: rgba(255, 200, 60, 0.15);
      border-color: rgba(255, 200, 60, 0.45);
      color: #ffd36a;
    }
    .zone-btn {
      margin-top: 8px; width: 100%; padding: 10px 12px;
      border-radius: 10px; border: 1px solid var(--line);
      background: rgba(255,255,255,0.04); color: var(--text);
      font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 0.85rem;
      cursor: pointer;
    }
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
      cursor: pointer;
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
    .help-lightbox {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 10000;
      background: rgba(2,6,12,0.92);
      align-items: center;
      justify-content: center;
      padding: 16px;
      flex-direction: column;
      gap: 12px;
    }
    .help-lightbox.open { display: flex; }
    .help-lightbox img {
      max-width: min(920px, 96vw);
      max-height: 72vh;
      object-fit: contain;
      border-radius: 8px;
      border: 1px solid rgba(148,163,184,0.25);
      background: #020617;
    }
    .help-lb-caption {
      color: #e2e8f0;
      font: 600 13px Space Grotesk, sans-serif;
      text-align: center;
    }
    .help-lb-nav {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .help-lb-nav button {
      border: 1px solid rgba(56,189,248,0.45);
      background: rgba(56,189,248,0.15);
      color: #e2e8f0;
      border-radius: 8px;
      padding: 8px 14px;
      font: 700 13px Space Grotesk, sans-serif;
      cursor: pointer;
    }
    .help-lb-count {
      color: #94a3b8;
      font: 500 12px Space Grotesk, sans-serif;
      min-width: 56px;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="top">
      <div class="brand">
        <div class="prohibit-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2c-.8 0-1.5.4-2 1L7.5 7H4c-1.1 0-2 .9-2 2v2c0 .6.4 1 1 1h1l1.2 6.2c.2 1 1 1.8 2 1.8h9.6c1 0 1.8-.8 2-1.8L20 12h1c.6 0 1-.4 1-1V9c0-1.1-.9-2-2-2h-3.5L14 3c-.5-.6-1.2-1-2-1zm-1.2 5.5L12 4.2l1.2 3.3H10.8zM7.1 14l-.6-3h11l-.6 3H7.1z"/></svg>
        </div>
        <div class="brand-text">
          <h1>Dog Detection</h1>
          <span class="tag">No Dogs Zone · Live Monitor</span>
        </div>
      </div>
      <div class="live-pill" id="livePill"><span class="dot"></span> STREAM</div>
    </header>

    <div class="layout">
      <div class="stage">
        <div class="zone-banner"><strong>PROHIBITED</strong> — Dogs not allowed</div>
        <div class="viewer">
          <span class="hud-corner tl"></span>
          <span class="hud-corner tr"></span>
          <span class="hud-corner bl"></span>
          <span class="hud-corner br"></span>
          <div class="alert-overlay">
            <div class="alert-badge">
              <span class="mini-prohibit" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M12 2c-.8 0-1.5.4-2 1L7.5 7H4c-1.1 0-2 .9-2 2v2c0 .6.4 1 1 1h1l1.2 6.2c.2 1 1 1.8 2 1.8h9.6c1 0 1.8-.8 2-1.8L20 12h1c.6 0 1-.4 1-1V9c0-1.1-.9-2-2-2h-3.5L14 3c-.5-.6-1.2-1-2-1zm-1.2 5.5L12 4.2l1.2 3.3H10.8zM7.1 14l-.6-3h11l-.6 3H7.1z"/></svg>
              </span>
              Dogs Prohibited
            </div>
          </div>
          <img id="stream" alt="stream">
          <canvas id="canvas"></canvas>
        </div>
      </div>

      <aside class="panel">
        <div class="panel-title">Status</div>
        <div class="row"><span class="label">TF.js</span><span class="value" id="tfStatus">Loading...</span></div>
        <div class="row"><span class="label">COCO-SSD</span><span class="value" id="modelStatus">Waiting...</span></div>
        <div class="row"><span class="label">Stream</span><span class="value" id="streamStatus">Connecting...</span></div>
        <div class="row"><span class="label">Dogs</span><span class="value" id="dogCount">0</span></div>
        <div class="row"><span class="label">Accuracy</span><span class="value" id="bestConf">—</span></div>
        <div class="row"><span class="label">Relay / Flash</span><span class="value" id="relayStatus">OFF</span></div>
        <div id="alertBox" class="status-box off">No Dog - Relay OFF</div>
        <button type="button" class="flash-btn" id="flashBtn">Flash LED: OFF</button>
        <button type="button" class="zone-btn" id="clearZoneBtn">Clear Detect Zone</button>
        <button type="button" class="help-btn" id="helpBtn" onclick="var o=document.getElementById('helpOverlay');if(o){o.style.display='flex';o.classList.add('open');o.setAttribute('aria-hidden','false');}">Help - Why this project?</button>
      </aside>
    </div>
    <footer class="project-footer">ESP32-CAM Dog Detection · Internship @ Evonto Solutions · Umesh Gaur</footer>
  </div>

  <div class="help-overlay" id="helpOverlay" aria-hidden="true">
    <div class="help-modal" role="dialog" aria-labelledby="helpTitle">
      <h2 id="helpTitle">Why this project?</h2>
      <p>This project was created to address a real problem: stray dogs often sit or sleep on car <b>roofs</b>.</p>
      <p>This can cause <b>damage</b> to the roof, leave <b>scratches and claw marks</b> on the paint, and sometimes even harm the <b>glass or windshield</b>.</p>
      <p>That is why this system uses an ESP32-CAM to detect dogs and trigger an alert (relay/flash) — so the vehicle stays protected.</p>
      <div class="help-grid">
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="Dogs sitting on a car roof and trunk"><span>Dogs sitting on a car roof and trunk</span></div>
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="Claw scratches on the car paint and hood"><span>Claw scratches on the car paint and hood</span></div>
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="A stray dog resting on a car roof"><span>A stray dog resting on a car roof</span></div>
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="Roof paint scratched by animal claws"><span>Roof paint scratched by animal claws</span></div>
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="Roof dent caused by heavy weight"><span>Roof dent caused by heavy weight</span></div>
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="Two dogs lying on a car roof"><span>Two dogs lying on a car roof</span></div>
<div class="help-card"><img src="data:image/jpeg;base64,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" alt="A dog sleeping on a car roof"><span>A dog sleeping on a car roof</span></div>
      </div>
      <button type="button" class="help-close" id="helpCloseBtn">Close</button>
    </div>
  </div>

  <div class="help-lightbox" id="helpLightbox" aria-hidden="true">
    <img id="helpLbImg" alt="">
    <div class="help-lb-caption" id="helpLbCaption"></div>
    <div class="help-lb-nav">
      <button type="button" id="helpLbPrev">Prev</button>
      <span class="help-lb-count" id="helpLbCount">1 / 1</span>
      <button type="button" id="helpLbNext">Next</button>
      <button type="button" id="helpLbClose">Close</button>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd@2.2.3"></script>
  <script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/blazeface@0.0.7/dist/blazeface.min.js"></script>
  <script>
    // Phone/WebView pe soft — screen pe dog photo bhi detect ho
    const DOG_CONF = 0.48;
    const PERSON_CONF = 0.35;
    const NEED_DOG_FRAMES = 2;
    const HOLD_MS = 7000;
    const RELAY_URL = '/relay';
    // Phone alert — cloud server (Railway) + ntfy backup
    // Railway URL deploy ke baad yahan daalo, example:
    // const ALERT_SERVER_URL = 'https://dog-alert-xxxx.up.railway.app';
    const ALERT_SERVER_URL = '';
    const ALERT_SECRET = 'YOUR_ALERT_SECRET';
    const NTFY_TOPIC = 'YOUR_NTFY_TOPIC';
    const NTFY_COOLDOWN_MS = 60000;
    let lastNtfyAt = 0;

    // Blocklist — kabhi bhi box/relay nahi
    const BLOCK = {
      person: 1, car: 1, truck: 1, bus: 1, motorcycle: 1, bicycle: 1,
      cat: 1, horse: 1, sheep: 1, cow: 1, bear: 1, bird: 1,
      backpack: 1, handbag: 1, suitcase: 1, umbrella: 1,
      chair: 1, couch: 1, bed: 1, 'dining table': 1,
      tv: 1, laptop: 1, cell: 1, 'cell phone': 1, book: 1,
      bottle: 1, cup: 1, bowl: 1, banana: 1, apple: 1
    };

    const streamImg = document.getElementById('stream');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');

    const tfStatus = document.getElementById('tfStatus');
    const modelStatus = document.getElementById('modelStatus');
    const streamStatus = document.getElementById('streamStatus');
    const dogCountEl = document.getElementById('dogCount');
    const bestConfEl = document.getElementById('bestConf');
    const relayStatusEl = document.getElementById('relayStatus');
    const alertBox = document.getElementById('alertBox');
    const flashBtn = document.getElementById('flashBtn');
    const clearZoneBtn = document.getElementById('clearZoneBtn');

    let model = null;
    let faceModel = null;
    let busy = false;
    let relayOn = false;
    let relayBusy = false;
    let holdUntil = 0;
    let dogSeenNow = false;
    let dogStreak = 0;

    // User-selected detect zone (canvas pixel coords). null = full frame
    let detectZone = null;   // { x, y, w, h }
    let drawingZone = false;
    let zoneStart = null;    // { x, y }
    let zoneDraft = null;    // while dragging

    function streamUrl() {
      return 'http://' + location.hostname + ':81/stream';
    }

    function canvasPoint(evt) {
      var e = evt.touches && evt.touches[0] ? evt.touches[0] : evt;
      var rect = canvas.getBoundingClientRect();
      var sx = canvas.width / Math.max(1, rect.width);
      var sy = canvas.height / Math.max(1, rect.height);
      return {
        x: Math.max(0, Math.min(canvas.width, (e.clientX - rect.left) * sx)),
        y: Math.max(0, Math.min(canvas.height, (e.clientY - rect.top) * sy))
      };
    }

    function normalizeRect(a, b) {
      var x1 = Math.min(a.x, b.x), y1 = Math.min(a.y, b.y);
      var x2 = Math.max(a.x, b.x), y2 = Math.max(a.y, b.y);
      return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
    }

    function pointInZone(cx, cy, zone) {
      if (!zone || zone.w < 8 || zone.h < 8) return true; // no zone = full frame
      return cx >= zone.x && cx <= zone.x + zone.w &&
             cy >= zone.y && cy <= zone.y + zone.h;
    }

    function drawDetectZone() {
      var z = zoneDraft || detectZone;
      if (!z || z.w < 2 || z.h < 2) return;
      ctx.save();
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = Math.max(2, Math.round(canvas.width / 220));
      ctx.setLineDash([8, 6]);
      ctx.strokeRect(z.x, z.y, z.w, z.h);
      ctx.fillStyle = 'rgba(56, 189, 248, 0.12)';
      ctx.fillRect(z.x, z.y, z.w, z.h);
      ctx.setLineDash([]);
      ctx.font = 'bold 13px Space Grotesk, sans-serif';
      ctx.fillStyle = '#38bdf8';
      ctx.fillText('DETECT ZONE', z.x + 6, Math.max(14, z.y - 6));
      ctx.restore();
    }

    function onZoneStart(evt) {
      evt.preventDefault();
      syncCanvas();
      drawingZone = true;
      zoneStart = canvasPoint(evt);
      zoneDraft = { x: zoneStart.x, y: zoneStart.y, w: 0, h: 0 };
    }
    function onZoneMove(evt) {
      if (!drawingZone || !zoneStart) return;
      evt.preventDefault();
      zoneDraft = normalizeRect(zoneStart, canvasPoint(evt));
      syncCanvas();
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      drawDetectZone();
    }
    function onZoneEnd(evt) {
      if (!drawingZone) return;
      evt.preventDefault();
      drawingZone = false;
      if (zoneDraft && zoneDraft.w >= 12 && zoneDraft.h >= 12) {
        detectZone = zoneDraft;
      }
      zoneDraft = null;
      zoneStart = null;
    }

    canvas.addEventListener('mousedown', onZoneStart);
    canvas.addEventListener('mousemove', onZoneMove);
    canvas.addEventListener('mouseup', onZoneEnd);
    canvas.addEventListener('mouseleave', onZoneEnd);
    canvas.addEventListener('touchstart', onZoneStart, { passive: false });
    canvas.addEventListener('touchmove', onZoneMove, { passive: false });
    canvas.addEventListener('touchend', onZoneEnd);
    canvas.addEventListener('touchcancel', onZoneEnd);

    if (clearZoneBtn) {
      clearZoneBtn.onclick = function () {
        detectZone = null;
        zoneDraft = null;
      };
    }

    function boxArea(b) {
      return Math.max(0, b[2]) * Math.max(0, b[3]);
    }

    function intersectionArea(a, b) {
      var ax2 = a[0] + a[2], ay2 = a[1] + a[3];
      var bx2 = b[0] + b[2], by2 = b[1] + b[3];
      var x1 = Math.max(a[0], b[0]);
      var y1 = Math.max(a[1], b[1]);
      var x2 = Math.min(ax2, bx2);
      var y2 = Math.min(ay2, by2);
      return Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
    }

    function expandBox(b, scale) {
      var cx = b[0] + b[2] / 2;
      var cy = b[1] + b[3] / 2;
      var nw = b[2] * scale;
      var nh = b[3] * scale;
      return [cx - nw / 2, cy - nh / 2, nw, nh];
    }

    function overlapsBox(dogB, otherB, minRatio) {
      var inter = intersectionArea(dogB, otherB);
      if (inter <= 0) return false;
      var dogA = boxArea(dogB);
      if (dogA <= 0) return false;
      if ((inter / dogA) >= minRatio) return true;
      var cx = dogB[0] + dogB[2] / 2;
      var cy = dogB[1] + dogB[3] / 2;
      return cx >= otherB[0] && cx <= otherB[0] + otherB[2] &&
             cy >= otherB[1] && cy <= otherB[1] + otherB[3];
    }

    function collectPeople(preds) {
      var people = [];
      for (var i = 0; i < preds.length; i++) {
        var p = preds[i];
        var name = String(p.class || '').toLowerCase().trim();
        if (name === 'person' && p.score >= PERSON_CONF) people.push(p);
      }
      return people;
    }

    function facesToBoxes(faces) {
      var boxes = [];
      if (!faces) return boxes;
      for (var i = 0; i < faces.length; i++) {
        var f = faces[i];
        // blazeface: topLeft / bottomRight as tensors or arrays
        var tl = f.topLeft;
        var br = f.bottomRight;
        if (tl && typeof tl.dataSync === 'function') tl = tl.dataSync();
        if (br && typeof br.dataSync === 'function') br = br.dataSync();
        if (!tl || !br) continue;
        var x = tl[0], y = tl[1];
        var w = br[0] - tl[0], h = br[1] - tl[1];
        if (w > 4 && h > 4) boxes.push([x, y, w, h]);
      }
      return boxes;
    }

    function isRealDog(p, people, faceBoxes) {
      if (!p) return false;
      var name = String(p.class || '').toLowerCase().trim();
      if (name !== 'dog') return false;
      if (BLOCK[name]) return false;
      if (!(p.score >= DOG_CONF)) return false;

      // Phone pe face reject soft — pehle dog detect ho
      if (faceBoxes && faceBoxes.length) {
        for (var f = 0; f < faceBoxes.length; f++) {
          if (overlapsBox(p.bbox, expandBox(faceBoxes[f], 1.1), 0.45)) return false;
        }
      }

      if (people && people.length) {
        for (var i = 0; i < people.length; i++) {
          if (overlapsBox(p.bbox, people[i].bbox, 0.5)) return false;
        }
      }
      return true;
    }

    function sendPhoneAlert(accuracyText) {
      var now = Date.now();
      if (now - lastNtfyAt < NTFY_COOLDOWN_MS) return;
      lastNtfyAt = now;
      var msg = 'Dog betha hai car pe!';
      var acc = (accuracyText && accuracyText !== '—') ? accuracyText : '';
      var body = acc ? (msg + ' Accuracy: ' + acc) : msg;

      // 1) Railway / cloud alert server → personal app (office / bahar)
      if (ALERT_SERVER_URL) {
        fetch(ALERT_SERVER_URL.replace(/\/$/, '') + '/alert', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-alert-secret': ALERT_SECRET
          },
          body: JSON.stringify({
            message: msg,
            accuracy: acc || undefined,
            secret: ALERT_SECRET
          })
        }).catch(function (e) { console.warn('Cloud alert failed', e); });
      }

      // 2) ntfy backup (optional — ntfy app subscribe)
      fetch('https://ntfy.sh/' + NTFY_TOPIC, {
        method: 'POST',
        headers: {
          'Title': 'Dog Alert',
          'Priority': 'high',
          'Tags': 'dog,warning'
        },
        body: body
      }).catch(function (e) { console.warn('ntfy alert failed', e); });
    }

    function setRelay(on) {
      if (relayOn === on || relayBusy) return;
      relayBusy = true;
      fetch(RELAY_URL + '?state=' + (on ? 'on' : 'off'), { cache: 'no-store' })
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          relayOn = on;
          relayStatusEl.textContent = on ? 'ON' : 'OFF';
          relayStatusEl.className = 'value ' + (on ? 'ok' : 'bad');
          document.body.classList.toggle('relay-on', on);
          console.log(on ? 'Dog Detected - Relay ON' : 'No Dog - Relay OFF');
          if (on) {
            sendPhoneAlert(bestConfEl ? bestConfEl.textContent : '');
          }
        })
        .catch(function (e) { console.warn('Relay error', e); })
        .finally(function () { relayBusy = false; });
    }

    function updateHoldUi() {
      var now = Date.now();
      if (holdUntil > now) {
        var left = Math.ceil((holdUntil - now) / 1000);
        alertBox.className = 'status-box on';
        alertBox.textContent = 'Dog Detected - Relay ON (' + left + 's)';
      } else if (relayOn) {
        alertBox.className = 'status-box on';
        alertBox.textContent = 'Dog Detected - Relay ON';
      } else {
        alertBox.className = 'status-box off';
        alertBox.textContent = 'No Dog - Relay OFF';
      }
    }

    function applyRelayLogic(dogPresent) {
      dogSeenNow = dogPresent;
      var now = Date.now();

      if (dogPresent && holdUntil <= now && !relayOn) {
        holdUntil = now + HOLD_MS;
        setRelay(true);
      } else if (dogPresent && holdUntil <= now && relayOn) {
        holdUntil = now + HOLD_MS;
        setRelay(true);
      } else if (!dogPresent && holdUntil <= now && relayOn) {
        setRelay(false);
      } else if (dogPresent && holdUntil > now) {
        setRelay(true);
      }
      updateHoldUi();
    }

    function syncCanvas() {
      var w = streamImg.naturalWidth || streamImg.clientWidth;
      var h = streamImg.naturalHeight || streamImg.clientHeight;
      if (w > 0 && h > 0 && (canvas.width !== w || canvas.height !== h)) {
        canvas.width = w;
        canvas.height = h;
      }
    }

    function drawOnlyDogs(predictions) {
      syncCanvas();
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Selected area (blue dashed) — dog sirf iske andar count
      drawDetectZone();

      var dogs = 0;
      var best = 0;
      var lw = Math.max(3, Math.round(canvas.width / 180));
      var zone = detectZone;

      for (var i = 0; i < predictions.length; i++) {
        var p = predictions[i];
        var name = String(p.class || '').toLowerCase().trim();

        // HARD FILTER: person / car / sab skip — box mat banao
        if (name !== 'dog') continue;
        if (!(p.score >= DOG_CONF)) continue;

        var x = p.bbox[0], y = p.bbox[1], w = p.bbox[2], h = p.bbox[3];
        var cx = x + w / 2;
        var cy = y + h / 2;

        // Zone select hai to sirf uske andar wale dog
        if (zone && !pointInZone(cx, cy, zone)) continue;

        dogs++;
        if (p.score > best) best = p.score;

        var pct = Math.round(p.score * 100);

        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = lw;
        ctx.strokeRect(x, y, w, h);

        var label = 'DOG ' + pct + '%';
        ctx.font = 'bold 16px Segoe UI, sans-serif';
        var tw = ctx.measureText(label).width + 10;
        var ly = Math.max(0, y - 24);
        ctx.fillStyle = 'rgba(34,197,94,0.92)';
        ctx.fillRect(x, ly, tw, 24);
        ctx.fillStyle = '#04110a';
        ctx.fillText(label, x + 5, ly + 17);
      }

      dogCountEl.textContent = String(dogs);
      bestConfEl.textContent = best > 0 ? Math.round(best * 100) + '%' : '—';

      // Streak: human flicker / 1-frame false dog se relay na chale
      if (dogs > 0) dogStreak++;
      else dogStreak = 0;
      applyRelayLogic(dogStreak >= NEED_DOG_FRAMES);
    }

    async function loop() {
      // iOS MJPEG: complete/naturalWidth unreliable — clientWidth bhi OK
      var ready = model && !busy && (
        streamImg.naturalWidth > 0 ||
        streamImg.clientWidth > 0
      );
      if (!ready) {
        requestAnimationFrame(loop);
        return;
      }
      busy = true;
      try {
        var preds = await model.detect(streamImg, 20, 0.25);
        var people = collectPeople(preds);

        var faceBoxes = [];
        if (faceModel && (dogStreak > 0 || (Date.now() % 400) < 120)) {
          try {
            var faces = await faceModel.estimateFaces(streamImg, false);
            faceBoxes = facesToBoxes(faces);
          } catch (fe) { /* soft-fail */ }
        }

        var dogsOnly = [];
        for (var i = 0; i < preds.length; i++) {
          if (isRealDog(preds[i], people, faceBoxes)) dogsOnly.push(preds[i]);
        }
        drawOnlyDogs(dogsOnly);
      } catch (e) {
        console.warn('detect error', e);
        dogStreak = 0;
        applyRelayLogic(false);
      }
      busy = false;
      setTimeout(function () { requestAnimationFrame(loop); }, 150);
    }

    setInterval(updateHoldUi, 200);

    function bindStream() {
      // Same-origin /capture blob — iOS pe stuck Connecting fix
      var captureBusy = false;
      var failCount = 0;
      var lastBlobUrl = '';

      function markLive() {
        streamStatus.textContent = 'Live';
        streamStatus.className = 'value ok';
        document.body.classList.add('is-live');
        syncCanvas();
      }

      function markRetry(msg) {
        streamStatus.textContent = msg || 'Retry...';
        streamStatus.className = 'value bad';
      }

      function captureUrl() {
        return 'http://' + location.hostname + '/capture?_=' + Date.now();
      }

      function pull() {
        if (captureBusy) return;
        captureBusy = true;
        var unlock = setTimeout(function () { captureBusy = false; }, 3000);

        fetch(captureUrl(), { cache: 'no-store' })
          .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.blob();
          })
          .then(function (blob) {
            var url = URL.createObjectURL(blob);
            var prev = lastBlobUrl;
            lastBlobUrl = url;
            streamImg.onload = function () {
              clearTimeout(unlock);
              captureBusy = false;
              failCount = 0;
              markLive();
              if (prev) {
                try { URL.revokeObjectURL(prev); } catch (e) {}
              }
            };
            streamImg.onerror = function () {
              clearTimeout(unlock);
              captureBusy = false;
              failCount++;
              markRetry('Retry ' + failCount);
              try { URL.revokeObjectURL(url); } catch (e) {}
            };
            streamImg.src = url;
          })
          .catch(function () {
            clearTimeout(unlock);
            captureBusy = false;
            failCount++;
            markRetry('Cam busy');
          });
      }

      setInterval(function () {
        if (streamImg.naturalWidth > 0) markLive();
      }, 1000);

      pull();
      setInterval(pull, 700);
    }

    async function boot() {
      detectZone = null;
      zoneDraft = null;
      bindStream();
      try {
        if (typeof tf === 'undefined') {
          tfStatus.textContent = 'FAILED';
          tfStatus.className = 'value bad';
          return;
        }
        tfStatus.textContent = 'OK';
        tfStatus.className = 'value ok';
        await tf.ready();

        modelStatus.textContent = 'Loading...';
        model = await cocoSsd.load({ base: 'lite_mobilenet_v2' });
        modelStatus.textContent = 'Ready';
        modelStatus.className = 'value ok';
        console.log('Ready: dog>=' + DOG_CONF);

        if (typeof blazeface !== 'undefined') {
          blazeface.load().then(function (m) {
            faceModel = m;
          }).catch(function () { faceModel = null; });
        }
        loop();
      } catch (e) {
        console.error(e);
        modelStatus.textContent = 'FAILED';
        modelStatus.className = 'value bad';
        alertBox.textContent = 'Model load fail — internet check karo';
      }
    }

    setRelay(false);

    // Help modal + photo gallery (detection UI untouched)
    (function () {
      var overlay = document.getElementById('helpOverlay');
      var closeBtn = document.getElementById('helpCloseBtn');
      var lb = document.getElementById('helpLightbox');
      var lbImg = document.getElementById('helpLbImg');
      var lbCap = document.getElementById('helpLbCaption');
      var lbCount = document.getElementById('helpLbCount');
      var cards = overlay ? overlay.querySelectorAll('.help-card') : [];
      var idx = 0;
      function closeHelp() {
        if (!overlay) return;
        overlay.classList.remove('open');
        overlay.style.display = 'none';
        overlay.setAttribute('aria-hidden', 'true');
      }
      function closeLb() {
        if (!lb) return;
        lb.classList.remove('open');
        lb.style.display = 'none';
        lb.setAttribute('aria-hidden', 'true');
      }
      function showLb(i) {
        if (!cards.length || !lb || !lbImg) return;
        idx = (i + cards.length) % cards.length;
        var img = cards[idx].querySelector('img');
        var span = cards[idx].querySelector('span');
        lbImg.src = img ? img.src : '';
        lbImg.alt = img ? (img.alt || '') : '';
        if (lbCap) lbCap.textContent = span ? span.textContent : (lbImg.alt || '');
        if (lbCount) lbCount.textContent = (idx + 1) + ' / ' + cards.length;
        lb.classList.add('open');
        lb.style.display = 'flex';
        lb.setAttribute('aria-hidden', 'false');
      }
      if (closeBtn) closeBtn.onclick = closeHelp;
      if (overlay) {
        overlay.addEventListener('click', function (e) {
          if (e.target === overlay) closeHelp();
        });
      }
      for (var c = 0; c < cards.length; c++) {
        (function (n) {
          cards[n].onclick = function () { showLb(n); };
        })(c);
      }
      var prev = document.getElementById('helpLbPrev');
      var next = document.getElementById('helpLbNext');
      var lbClose = document.getElementById('helpLbClose');
      if (prev) prev.onclick = function () { showLb(idx - 1); };
      if (next) next.onclick = function () { showLb(idx + 1); };
      if (lbClose) lbClose.onclick = closeLb;
      if (lb) {
        lb.addEventListener('click', function (e) {
          if (e.target === lb) closeLb();
        });
      }
      document.addEventListener('keydown', function (e) {
        if (!lb || lb.style.display !== 'flex') return;
        if (e.key === 'ArrowRight') showLb(idx + 1);
        if (e.key === 'ArrowLeft') showLb(idx - 1);
        if (e.key === 'Escape') closeLb();
      });
    })();

    // Camera flash LED button (GPIO4) — detection logic alag
    if (flashBtn) {
      flashBtn.onclick = function () {
        fetch('/led?state=toggle', { cache: 'no-store' })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            var on = j.led === 'on';
            flashBtn.textContent = on ? 'Flash LED: ON' : 'Flash LED: OFF';
            flashBtn.className = on ? 'flash-btn on' : 'flash-btn';
          })
          .catch(function (e) { console.warn('LED error', e); });
      };
    }

    boot();
  </script>
</body>
</html>
)rawliteral";

#endif
