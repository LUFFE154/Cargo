from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


ui_router = APIRouter(tags=["ui"])


def _layout(title: str, page: str, content: str) -> HTMLResponse:
    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    />

    <meta
        name="theme-color"
        content="#0d0f10"
    />

    <title>{title}</title>

    <link
        rel="stylesheet"
        href="/static/app.css"
    />
</head>

<body data-page="{page}">

    <div class="app-shell">

        <header class="topbar">

            <a class="brand" href="/">
                <span class="brand-mark">
                <img src="static/logo.png" alt="Cargo">
                </span>
                <span>Cargo</span>
            </a>


            <nav class="nav-links">
                <a href="/">Home</a>
                <a href="/upload">Upload</a>
                <a href="/files">My Files</a>
                <a href="/download">Download</a>
            </nav>


            <div class="auth-panel">

                <div
                    class="auth-status"
                    id="authStatus"
                >
                    Not signed in
                </div>


                <form
                    class="auth-form"
                    id="authForm"
                >

                    <input
                        type="email"
                        name="email"
                        placeholder="Email"
                        autocomplete="email"
                        required
                    />

                    <input
                        type="password"
                        name="password"
                        placeholder="Password"
                        autocomplete="current-password"
                        minlength="8"
                        required
                    />

                    <button
                        type="submit"
                        class="btn btn-secondary"
                    >
                        Sign in
                    </button>

                    <button
                        type="button"
                        class="btn btn-ghost"
                        id="registerButton"
                    >
                        Create account
                    </button>

                </form>

            </div>

        </header>


        <main
            class="page"
            data-page="{page}"
        >
            {content}
        </main>

    </div>


    <div
        id="toastHost"
        class="toast-host"
    ></div>


    <script
        src="/static/app.js"
        defer
    ></script>

</body>
</html>"""

    return HTMLResponse(html)


@ui_router.get("/", response_class=HTMLResponse)
async def home_page() -> HTMLResponse:

    content = """
    <section class="hero card reveal">

        <div class="hero-copy">

            <p class="eyebrow">
                Private file transfer
            </p>

            <h1>
                Move files between your devices without sending them to the cloud.
            </h1>

            <p class="lede">
                Cargo lets you upload a file, generate a short transfer code,
                and move it to another device on your network.
            </p>

            <div class="hero-actions">

                <a
                    class="btn btn-primary"
                    href="/upload"
                >
                    Upload a file
                </a>

                <a
                    class="btn btn-secondary"
                    href="/download"
                >
                    Download a file
                </a>

            </div>

        </div>


        <div class="hero-panel">

            <div class="stat">
                <span>Transfer code</span>
                <strong>6 characters</strong>
            </div>

            <div class="stat">
                <span>Access</span>
                <strong>Code or QR</strong>
            </div>

            <div class="stat">
                <span>Storage</span>
                <strong>Your server</strong>
            </div>

        </div>

    </section>


    <section class="grid three-up">

        <article class="card reveal delay-1">

            <h2>Upload</h2>

            <p>
                Choose a file and Cargo creates a temporary transfer for it.
            </p>

        </article>


        <article class="card reveal delay-2">

            <h2>Share</h2>

            <p>
                Give the other device the transfer code or let it scan the QR code.
            </p>

        </article>


        <article class="card reveal delay-3">

            <h2>Download</h2>

            <p>
                Enter the code on the destination device and retrieve the file.
            </p>

        </article>

    </section>
    """

    return _layout(
        "Cargo - Home",
        "home",
        content,
    )


@ui_router.get("/upload", response_class=HTMLResponse)
async def upload_page() -> HTMLResponse:

    content = """
    <section class="page-head reveal">

        <div>

            <p class="eyebrow">
                Upload
            </p>

            <h1>
                Send a file to another device.
            </h1>

            <p class="lede">
                Select a file, choose how long the transfer should remain available,
                and Cargo will generate a transfer code for you.
            </p>

        </div>

    </section>


    <section class="grid upload-grid">

        <article class="card upload-card reveal">

            <form
                id="uploadForm"
                class="upload-form"
            >

                <div
                    id="dropZone"
                    class="drop-zone"
                >

                    <input
                        id="uploadFile"
                        name="file"
                        type="file"
                        hidden
                        required
                    />

                    <div class="drop-zone-inner">

                        <div class="drop-icon">
                            ⇪
                        </div>

                        <h2>
                            Drop your file here
                        </h2>

                        <p>
                            or click to choose a file
                        </p>

                    </div>

                </div>


                <label class="field">

                    <span>
                        Keep transfer available for
                    </span>

                    <input
                        id="expiresInSeconds"
                        type="number"
                        min="60"
                        step="60"
                        value="3600"
                    />

                </label>


                <button
                    type="submit"
                    class="btn btn-primary btn-wide"
                >
                    Create transfer
                </button>


                <div class="progress-wrap">

                    <div class="progress-label">

                        <span>
                            Upload progress
                        </span>

                        <strong id="uploadProgressText">
                            0%
                        </strong>

                    </div>

                    <div class="progress">

                        <div
                            id="uploadProgressBar"
                            class="progress-bar"
                            style="width: 0%"
                        ></div>

                    </div>

                </div>

            </form>

        </article>


        <article
            class="card result-card reveal delay-1"
            id="uploadResultCard"
        >

            <div class="section-title">

                <h2>
                    Transfer ready
                </h2>

                <p id="uploadResultHint">
                    Your transfer details will appear here after the upload.
                </p>

            </div>


            <div
                class="result-code"
                id="transferCode"
            >
                ------
            </div>


            <div class="result-actions">

                <button
                    class="btn btn-secondary"
                    id="copyCodeButton"
                    disabled
                >
                    Copy code
                </button>

                <a
                    class="btn btn-ghost"
                    id="downloadLink"
                    href="#"
                    target="_blank"
                    rel="noreferrer"
                    aria-disabled="true"
                >
                    Open download
                </a>

            </div>


            <div class="qr-frame">

                <img
                    id="qrCodeImage"
                    alt="Transfer QR code"
                />

            </div>

        </article>

    </section>
    """

    return _layout(
        "Cargo - Upload",
        "upload",
        content,
    )


@ui_router.get("/files", response_class=HTMLResponse)
async def files_page() -> HTMLResponse:

    content = """
    <section class="page-head reveal">

        <div>

            <p class="eyebrow">
                My Files
            </p>

            <h1>
                Files you've sent with Cargo.
            </h1>

            <p class="lede">
                Keep track of your transfers, their status, and how long they
                remain available.
            </p>

        </div>

    </section>


    <section class="card reveal">

        <div class="section-title">

            <div>

                <h2>
                    Your transfers
                </h2>

                <p id="filesListHint">
                    Loading your files...
                </p>

            </div>


            <div class="files-search">

                <input
                    id="filesSearch"
                    type="search"
                    placeholder="Search files..."
                    autocomplete="off"
                />

            </div>

        </div>


        <div
            id="filesList"
            class="files-list"
            aria-live="polite"
        ></div>


        <div
            id="filesEmpty"
            class="files-empty"
            hidden
        >

            <h2>
                No files yet
            </h2>

            <p>
                Files you upload will appear here.
            </p>

            <a
                class="btn btn-primary"
                href="/upload"
            >
                Upload your first file
            </a>

        </div>

    </section>
    """

    return _layout(
        "Cargo - My Files",
        "files",
        content,
    )


@ui_router.get("/download", response_class=HTMLResponse)
async def download_page() -> HTMLResponse:

    content = """
    <section class="page-head reveal">

        <div>

            <p class="eyebrow">
                Download
            </p>

            <h1>
                Retrieve a file with its transfer code.
            </h1>

            <p class="lede">
                Enter the code you received to check the transfer and download
                the file.
            </p>

        </div>

    </section>


    <section class="grid download-grid">

        <article class="card reveal">

            <form
                id="downloadForm"
                class="download-form"
            >

                <label class="field">

                    <span>
                        Transfer code
                    </span>

                    <input
                        id="downloadCode"
                        type="text"
                        maxlength="6"
                        minlength="6"
                        placeholder="ABC123"
                        autocomplete="off"
                    />

                </label>


                <button
                    type="submit"
                    class="btn btn-primary btn-wide"
                >
                    Download file
                </button>


                <div class="progress-wrap">

                    <div class="progress-label">

                        <span>
                            Download progress
                        </span>

                        <strong id="downloadProgressText">
                            0%
                        </strong>

                    </div>

                    <div class="progress">

                        <div
                            id="downloadProgressBar"
                            class="progress-bar progress-bar-download"
                            style="width: 0%"
                        ></div>

                    </div>

                </div>

            </form>

        </article>


        <article
            class="card reveal delay-1"
            id="downloadInfoCard"
        >

            <div class="section-title">

                <h2>
                    File info
                </h2>

                <p id="downloadInfoHint">
                    Enter a transfer code to see its details.
                </p>

            </div>


            <div class="info-list">

                <div>

                    <span>
                        Name
                    </span>

                    <strong id="downloadFileName">
                        —
                    </strong>

                </div>


                <div>

                    <span>
                        Size
                    </span>

                    <strong id="downloadFileSize">
                        —
                    </strong>

                </div>


                <div>

                    <span>
                        Status
                    </span>

                    <strong id="downloadFileStatus">
                        —
                    </strong>

                </div>

            </div>

        </article>

    </section>
    """

    return _layout(
        "Cargo - Download",
        "download",
        content,
    )