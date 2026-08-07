from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui_router = APIRouter(tags=["ui"])


def _layout(title: str, page: str, content: str) -> HTMLResponse:
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#0f172a" />
  <title>{title}</title>
  <link rel="stylesheet" href="/static/app.css" />
</head>
<body data-page="{page}">
  <div class="bg-orb bg-orb-a"></div>
  <div class="bg-orb bg-orb-b"></div>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="/">
        <span class="brand-mark">C</span>
        <span>Cargo</span>
      </a>
      <nav class="nav-links">
        <a href="/">Home</a>
        <a href="/upload">Upload</a>
        <a href="/download">Download</a>
      </nav>
      <div class="auth-panel">
        <div class="auth-status" id="authStatus">Not signed in</div>
        <form class="auth-form" id="authForm">
          <input type="email" name="email" placeholder="Email" required />
          <input type="password" name="password" placeholder="Password" minlength="8" required />
          <button type="submit" class="btn btn-secondary">Sign in</button>
          <button type="button" class="btn btn-ghost" id="registerButton">Create account</button>
        </form>
      </div>
    </header>
    <main class="page" data-page="{page}">
      {content}
    </main>
  </div>
  <div id="toastHost" class="toast-host"></div>
  <script src="/static/app.js" defer></script>
</body>
</html>"""
    return HTMLResponse(html)


@ui_router.get("/", response_class=HTMLResponse)
async def home_page() -> HTMLResponse:
    content = """
    <section class="hero card reveal">
      <div class="hero-copy">
        <p class="eyebrow">Local-first file transfer</p>
        <h1>Send files across your LAN in seconds.</h1>
        <p class="lede">Upload a file, get a short transfer code and QR code, then download it on another device without cloud storage.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="/upload">Upload a file</a>
          <a class="btn btn-secondary" href="/download">Download with code</a>
        </div>
      </div>
      <div class="hero-panel">
        <div class="stat">
          <span>Transfer code</span>
          <strong>6 characters</strong>
        </div>
        <div class="stat">
          <span>Storage</span>
          <strong>Disk + PostgreSQL</strong>
        </div>
        <div class="stat">
          <span>Sharing</span>
          <strong>QR + code + link</strong>
        </div>
      </div>
    </section>
    <section class="grid three-up">
      <article class="card reveal delay-1">
        <h2>1. Upload</h2>
        <p>Drag a file into the upload zone and Cargo stores it on disk while preparing metadata.</p>
      </article>
      <article class="card reveal delay-2">
        <h2>2. Share</h2>
        <p>Copy the transfer code or scan the QR code to move the file to another computer.</p>
      </article>
      <article class="card reveal delay-3">
        <h2>3. Download</h2>
        <p>Enter the code on the second device and stream the file immediately from the LAN.</p>
      </article>
    </section>
    """
    return _layout("Cargo - Home", "home", content)


@ui_router.get("/upload", response_class=HTMLResponse)
async def upload_page() -> HTMLResponse:
    content = """
    <section class="page-head reveal">
      <div>
        <p class="eyebrow">Upload</p>
        <h1>Drop a file to create a transfer code.</h1>
        <p class="lede">Upload progress is tracked live. When the file finishes, Cargo shows the code, copy button, and QR code.</p>
      </div>
    </section>
    <section class="grid upload-grid">
      <article class="card upload-card reveal">
        <form id="uploadForm" class="upload-form">
          <div id="dropZone" class="drop-zone">
            <input id="uploadFile" name="file" type="file" hidden required />
            <div class="drop-zone-inner">
              <div class="drop-icon">⇪</div>
              <h2>Drag & drop your file here</h2>
              <p>or click to browse your device</p>
            </div>
          </div>
          <label class="field">
            <span>Auto-expire after seconds</span>
            <input id="expiresInSeconds" type="number" min="60" step="60" value="3600" />
          </label>
          <button type="submit" class="btn btn-primary btn-wide">Create transfer</button>
          <div class="progress-wrap">
            <div class="progress-label"><span>Upload progress</span><strong id="uploadProgressText">0%</strong></div>
            <div class="progress"><div id="uploadProgressBar" class="progress-bar" style="width:0%"></div></div>
          </div>
        </form>
      </article>
      <article class="card result-card reveal delay-1" id="uploadResultCard">
        <div class="section-title">
          <h2>Transfer ready</h2>
          <p id="uploadResultHint">Your transfer code appears here after upload.</p>
        </div>
        <div class="result-code" id="transferCode">------</div>
        <div class="result-actions">
          <button class="btn btn-secondary" id="copyCodeButton" disabled>Copy code</button>
          <a class="btn btn-ghost" id="downloadLink" href="#" target="_blank" rel="noreferrer" aria-disabled="true">Open download</a>
        </div>
        <div class="qr-frame">
          <img id="qrCodeImage" alt="Transfer QR code" />
        </div>
      </article>
    </section>
    """
    return _layout("Cargo - Upload", "upload", content)


@ui_router.get("/download", response_class=HTMLResponse)
async def download_page() -> HTMLResponse:
    content = """
    <section class="page-head reveal">
      <div>
        <p class="eyebrow">Download</p>
        <h1>Enter a transfer code to start the download.</h1>
        <p class="lede">Cargo resolves the code, shows file details, and streams the file with a progress bar.</p>
      </div>
    </section>
    <section class="grid download-grid">
      <article class="card reveal">
        <form id="downloadForm" class="download-form">
          <label class="field">
            <span>Transfer code</span>
            <input id="downloadCode" type="text" maxlength="6" minlength="6" placeholder="ABC123" autocomplete="off" />
          </label>
          <button type="submit" class="btn btn-primary btn-wide">Download file</button>
          <div class="progress-wrap">
            <div class="progress-label"><span>Download progress</span><strong id="downloadProgressText">0%</strong></div>
            <div class="progress"><div id="downloadProgressBar" class="progress-bar progress-bar-download" style="width:0%"></div></div>
          </div>
        </form>
      </article>
      <article class="card reveal delay-1" id="downloadInfoCard">
        <div class="section-title">
          <h2>File info</h2>
          <p id="downloadInfoHint">Resolve a code to see the file name, size, and expiration.</p>
        </div>
        <div class="info-list">
          <div><span>Name</span><strong id="downloadFileName">—</strong></div>
          <div><span>Size</span><strong id="downloadFileSize">—</strong></div>
          <div><span>Status</span><strong id="downloadFileStatus">—</strong></div>
        </div>
      </article>
    </section>
    """
    return _layout("Cargo - Download", "download", content)
