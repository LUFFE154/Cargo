const API_PREFIX = '/api/v1';
const TOKEN_KEY = 'cargo.access_token';

function $(id) {
  return document.getElementById(id);
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
  refreshAuthStatus();
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  refreshAuthStatus();
}

function decodeJwtPayload(token) {
  try {
    const payload = token.split('.')[1];
    const json = atob(
      payload.replaceAll('-', '+').replaceAll('_', '/')
    );

    return JSON.parse(
      decodeURIComponent(
        Array.from(
          json,
          (char) =>
            `%${char.codePointAt(0).toString(16).padStart(2, '0')}`
        ).join('')
      )
    );
  } catch {
    return null;
  }
}

function toast(message, kind = 'success') {
  const host = $('toastHost');

  if (!host) return;

  const node = document.createElement('div');
  node.className = `toast ${kind}`;
  node.textContent = message;

  host.appendChild(node);

  window.setTimeout(() => node.remove(), 4600);
}

function getCurrentUser() {
  const token = getToken();

  if (!token) {
    return null;
  }

  return decodeJwtPayload(token);
}

function refreshAuthStatus() {
  const status = $('authStatus');

  if (!status) return;

  const user = getCurrentUser();

  if (!user) {
    status.textContent = 'Not signed in';
    status.classList.remove('signed-in');
    return;
  }

  status.textContent = user.email
    ? `Signed in as ${user.email}`
    : 'Signed in';

  status.classList.add('signed-in');
}

function setButtonLoading(button, isLoading) {
  if (!button) return;

  button.classList.toggle('is-loading', isLoading);
  button.disabled = isLoading;
}

async function submitAuth(form, mode) {
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  const response = await fetch(
    `${API_PREFIX}/auth/${mode}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || 'Authentication failed'
    );
  }

  return response.json();
}

function getLoginRedirect() {
  const params = new URLSearchParams(window.location.search);
  const next = params.get('next');

  if (!next || !next.startsWith('/')) {
    return '/';
  }

  return next;
}

function redirectToLogin() {
  const currentPath =
    window.location.pathname +
    window.location.search;

  const params = new URLSearchParams();

  params.set('next', currentPath);

  window.location.href =
    `/login?${params.toString()}`;
}

function bindAuthForm() {
  const form = $('authForm');
  const registerButton = $('registerButton');

  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const button =
      form.querySelector('button[type="submit"]');

    setButtonLoading(button, true);

    try {
      const result = await submitAuth(form, 'login');

      setToken(result.access_token);

      toast('Signed in successfully.');

      if (document.body.dataset.page === 'login') {
        window.location.href = getLoginRedirect();
      }
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      setButtonLoading(button, false);
    }
  });

  if (!registerButton) return;

  registerButton.addEventListener('click', async (event) => {
    event.preventDefault();

    setButtonLoading(registerButton, true);

    try {
      const result =
        await submitAuth(form, 'register');

      setToken(result.access_token);

      toast('Account created successfully.');

      if (document.body.dataset.page === 'login') {
        window.location.href = getLoginRedirect();
      }
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      setButtonLoading(registerButton, false);
    }
  });
}

function setupProtectedUpload() {
  const form = $('uploadForm');

  if (!form) return;

  if (!getToken()) {
    form.addEventListener(
      'submit',
      (event) => {
        event.preventDefault();
        redirectToLogin();
      },
      { once: true }
    );
  }
}

function setupUploadPage() {
  const form = $('uploadForm');
  const dropZone = $('dropZone');
  const fileInput = $('uploadFile');
  const progressBar = $('uploadProgressBar');
  const progressText = $('uploadProgressText');
  const transferCode = $('transferCode');
  const qrCodeImage = $('qrCodeImage');
  const copyButton = $('copyCodeButton');
  const downloadLink = $('downloadLink');
  const resultHint = $('uploadResultHint');

  if (!form || !dropZone || !fileInput) {
    return;
  }

  const dropIconEl =
    dropZone.querySelector('.drop-icon');

  let filenameTag = null;

  function showSelectedFile(file) {
    if (!file) return;

    dropZone.classList.add('has-file');

    if (!filenameTag) {
      filenameTag = document.createElement('span');
      filenameTag.className = 'drop-filename';

      const inner =
        dropZone.querySelector('.drop-zone-inner') ||
        dropZone;

      inner.appendChild(filenameTag);
    }

    const sizeMb =
      (file.size / (1024 * 1024)).toFixed(2);

    filenameTag.textContent =
      `${file.name} · ${sizeMb} MB`;

    toast(`${file.name} selected.`);
  }

  dropZone.addEventListener('click', () => {
    fileInput.click();
  });

  dropZone.addEventListener('keydown', (event) => {
    if (
      event.key === 'Enter' ||
      event.key === ' '
    ) {
      event.preventDefault();
      fileInput.click();
    }
  });

  ['dragenter', 'dragover'].forEach(
    (eventName) => {
      dropZone.addEventListener(
        eventName,
        (event) => {
          event.preventDefault();
          dropZone.classList.add('dragover');
        }
      );
    }
  );

  ['dragleave', 'drop'].forEach(
    (eventName) => {
      dropZone.addEventListener(
        eventName,
        (event) => {
          event.preventDefault();
          dropZone.classList.remove('dragover');
        }
      );
    }
  );

  dropZone.addEventListener('drop', (event) => {
    const dataTransfer = new DataTransfer();

    Array.from(event.dataTransfer.files)
      .forEach((file) => {
        dataTransfer.items.add(file);
      });

    fileInput.files = dataTransfer.files;

    showSelectedFile(fileInput.files[0]);
  });

  fileInput.addEventListener('change', () => {
    showSelectedFile(fileInput.files[0]);
  });

  copyButton?.addEventListener(
    'click',
    async () => {
      try {
        await navigator.clipboard.writeText(
          transferCode.textContent.trim()
        );

        const original =
          copyButton.textContent;

        copyButton.textContent = 'Copied';
        copyButton.classList.add('copied');

        toast('Transfer code copied.');

        window.setTimeout(() => {
          copyButton.textContent = original;
          copyButton.classList.remove('copied');
        }, 1600);
      } catch {
        toast(
          'Could not copy code.',
          'error'
        );
      }
    }
  );

  form.addEventListener(
    'submit',
    (event) => {
      event.preventDefault();

      const file = fileInput.files[0];

      if (!file) {
        toast(
          'Choose a file first.',
          'error'
        );
        return;
      }

      const token = getToken();

      if (!token) {
        redirectToLogin();
        return;
      }

      const submitButton =
        form.querySelector(
          'button[type="submit"]'
        );

      setButtonLoading(
        submitButton,
        true
      );

      progressBar.style.width = '0%';
      progressText.textContent = '0%';

      const xhr = new XMLHttpRequest();

      const formData = new FormData();

      formData.append('file', file);

      formData.append(
        'expires_in_seconds',
        $('expiresInSeconds').value || '3600'
      );

      xhr.open(
        'POST',
        `${API_PREFIX}/transfers`
      );

      xhr.setRequestHeader(
        'Authorization',
        `Bearer ${token}`
      );

      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return;

        const percent = Math.round(
          (event.loaded / event.total) * 100
        );

        progressBar.style.width =
          `${percent}%`;

        progressText.textContent =
          `${percent}%`;
      };

      xhr.onload = () => {
        setButtonLoading(
          submitButton,
          false
        );

        if (
          xhr.status === 401 ||
          xhr.status === 403
        ) {
          clearToken();
          redirectToLogin();
          return;
        }

        if (
          xhr.status < 200 ||
          xhr.status >= 300
        ) {
          toast(
            'Upload failed.',
            'error'
          );
          return;
        }

        const result =
          JSON.parse(xhr.responseText);

        transferCode.textContent =
          result.transfer_code;

        resultHint.textContent =
          `Uploaded ${result.original_name}. ` +
          'Share the code with the other device.';

        copyButton.disabled = false;

        downloadLink.href =
          `${API_PREFIX}/transfers/` +
          `${result.transfer_code}/download`;

        downloadLink.setAttribute(
          'aria-disabled',
          'false'
        );

        qrCodeImage.src =
          `${API_PREFIX}/transfers/` +
          `${result.transfer_code}/qr.png`;

        progressBar.style.width = '100%';
        progressText.textContent = '100%';

        toast(
          'Transfer created successfully.'
        );
      };

      xhr.onerror = () => {
        setButtonLoading(
          submitButton,
          false
        );

        toast(
          'Upload failed.',
          'error'
        );
      };

      xhr.send(formData);
    }
  );
}

function setupFilesPage() {
  const filesList = $('filesList');
  const filesEmpty = $('filesEmpty');
  const filesSearch = $('filesSearch');
  const filesListHint = $('filesListHint');

  if (!filesList) return;

  let transfers = [];

  function formatFileSize(bytes) {
    if (!Number.isFinite(bytes) || bytes < 0) {
      return 'Unknown size';
    }

    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    if (bytes < 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  function formatExpiration(expiresAt) {
    if (!expiresAt) {
      return {
        text: 'No expiration',
        className: 'file-expiration'
      };
    }

    const expiration = new Date(expiresAt);
    const now = new Date();

    if (Number.isNaN(expiration.getTime())) {
      return {
        text: 'Expiration unavailable',
        className: 'file-expiration'
      };
    }

    const difference = expiration.getTime() - now.getTime();

    if (difference <= 0) {
      return {
        text: 'Expired',
        className: 'file-expiration expired'
      };
    }

    const minutes = Math.floor(difference / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return {
        text: `Expires in ${days} day${days === 1 ? '' : 's'}`,
        className: 'file-expiration'
      };
    }

    if (hours > 0) {
      return {
        text: `Expires in ${hours} hour${hours === 1 ? '' : 's'}`,
        className: hours < 2
          ? 'file-expiration expiring-soon'
          : 'file-expiration'
      };
    }

    return {
      text: `Expires in ${Math.max(minutes, 1)} minute${minutes === 1 ? '' : 's'}`,
      className: 'file-expiration expiring-soon'
    };
  }

  function formatStatus(status) {
    const labels = {
      uploading: 'Uploading',
      processing: 'Processing',
      ready: 'Ready',
      downloaded: 'Downloaded',
      expired: 'Expired',
      failed: 'Failed'
    };

    return labels[status] || status || 'Unknown';
  }

  function createFileCard(transfer) {
    const card = document.createElement('article');
    card.className = 'file-card';

    const expiration = formatExpiration(transfer.expires_at);
    const status = formatStatus(transfer.status);

    const header = document.createElement('div');
    header.className = 'file-card-header';

    const name = document.createElement('h3');
    name.className = 'file-name';
    name.textContent = transfer.original_name || 'Unnamed file';

    const statusBadge = document.createElement('span');
    statusBadge.className = `file-status ${transfer.status || ''}`;
    statusBadge.textContent = status;

    header.appendChild(name);
    header.appendChild(statusBadge);

    const details = document.createElement('div');
    details.className = 'file-details';

    const size = document.createElement('span');
    size.textContent = formatFileSize(transfer.size_bytes);

    const code = document.createElement('span');
    code.textContent = `Code: ${transfer.transfer_code}`;

    details.appendChild(size);
    details.appendChild(code);

    const footer = document.createElement('div');
    footer.className = 'file-card-footer';

    const expirationElement = document.createElement('span');
    expirationElement.className = expiration.className;
    expirationElement.textContent = expiration.text;

    const actions = document.createElement('div');
    actions.className = 'file-actions';

    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-ghost';
    copyButton.textContent = 'Copy code';

    copyButton.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(transfer.transfer_code);

        const originalText = copyButton.textContent;
        copyButton.textContent = 'Copied';

        toast('Transfer code copied.');

        window.setTimeout(() => {
          copyButton.textContent = originalText;
        }, 1600);
      } catch {
        toast('Could not copy code.', 'error');
      }
    });

    actions.appendChild(copyButton);

    if (expiration.text !== 'Expired') {
      const downloadButton = document.createElement('a');
      downloadButton.className = 'btn btn-secondary';
      downloadButton.href = '/download';
      downloadButton.textContent = 'Download';

      actions.appendChild(downloadButton);
    }

    footer.appendChild(expirationElement);
    footer.appendChild(actions);

    card.appendChild(header);
    card.appendChild(details);
    card.appendChild(footer);

    return card;
  }

  function renderTransfers(list) {
    filesList.innerHTML = '';

    if (!list.length) {
      filesEmpty.hidden = false;
      filesList.hidden = true;

      if (transfers.length > 0) {
        filesListHint.textContent = 'No files match your search.';
      } else {
        filesListHint.textContent = 'You have not uploaded any files yet.';
      }

      return;
    }

    filesEmpty.hidden = true;
    filesList.hidden = false;

    filesListHint.textContent =
      `${list.length} file${list.length === 1 ? '' : 's'}`;

    list.forEach((transfer) => {
      filesList.appendChild(createFileCard(transfer));
    });
  }

  async function loadTransfers() {
    const token = getToken();

    if (!token) {
      filesList.hidden = true;
      filesEmpty.hidden = false;

      filesListHint.textContent = 'Sign in to view your files.';

      filesEmpty.innerHTML = `
        <h2>Sign in required</h2>
        <p>
          Your uploaded files are linked to your account.
          Sign in above to see them here.
        </p>
      `;

      return;
    }

    try {
      filesListHint.textContent = 'Loading your files...';

      const response = await fetch(
        `${API_PREFIX}/transfers/mine`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.status === 401) {
        clearToken();
        throw new Error('Your session has expired. Please sign in again.');
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(
          error.detail || 'Could not load your files.'
        );
      }

      transfers = await response.json();

      renderTransfers(transfers);
    } catch (error) {
      filesList.hidden = true;
      filesEmpty.hidden = false;

      filesListHint.textContent = 'Could not load your files.';

      filesEmpty.innerHTML = `
        <h2>Something went wrong</h2>
        <p>${error.message}</p>
      `;
    }
  }

  filesSearch?.addEventListener('input', () => {
    const query = filesSearch.value.trim().toLowerCase();

    if (!query) {
      renderTransfers(transfers);
      return;
    }

    const filtered = transfers.filter((transfer) => {
      const name = (transfer.original_name || '').toLowerCase();
      const code = (transfer.transfer_code || '').toLowerCase();

      return name.includes(query) || code.includes(query);
    });

    renderTransfers(filtered);
  });

  loadTransfers();
}

function setupDownloadPage() {
  const form = $('downloadForm');
  const progressBar =
    $('downloadProgressBar');
  const progressText =
    $('downloadProgressText');
  const infoName =
    $('downloadFileName');
  const infoSize =
    $('downloadFileSize');
  const infoStatus =
    $('downloadFileStatus');
  const codeInput =
    $('downloadCode');

  if (!form) return;

  codeInput?.addEventListener(
    'input',
    () => {
      codeInput.classList.remove('error');

      codeInput.value =
        codeInput.value.toUpperCase();
    }
  );

  form.addEventListener(
    'submit',
    async (event) => {
      event.preventDefault();

      const code =
        codeInput.value
          .trim()
          .toUpperCase();

      if (code.length !== 6) {
        codeInput.classList.add(
          'error'
        );

        toast(
          'Enter a 6-character transfer code.',
          'error'
        );

        return;
      }

      const submitButton =
        form.querySelector(
          'button[type="submit"]'
        );

      setButtonLoading(
        submitButton,
        true
      );

      progressBar.style.width = '0%';
      progressText.textContent = '0%';

      try {
        const metadataResponse =
          await fetch(
            `${API_PREFIX}/transfers/${code}`
          );

        if (!metadataResponse.ok) {
          throw new Error(
            'Transfer code not found'
          );
        }

        const metadata =
          await metadataResponse.json();

        codeInput.classList.remove(
          'error'
        );

        infoName.textContent =
          metadata.original_name;

        infoSize.textContent =
          `${(
            metadata.size_bytes /
            (1024 * 1024)
          ).toFixed(2)} MB`;

        infoStatus.textContent =
          metadata.status;

        const response =
          await fetch(
            `${API_PREFIX}/transfers/` +
            `${code}/download`
          );

        if (
          !response.ok ||
          !response.body
        ) {
          throw new Error(
            'Download failed'
          );
        }

        const total = Number(
          response.headers.get(
            'content-length'
          ) ||
          metadata.size_bytes ||
          '0'
        );

        const reader =
          response.body.getReader();

        const chunks = [];

        let received = 0;

        while (true) {
          const {
            done,
            value,
          } = await reader.read();

          if (done) break;

          chunks.push(value);

          received += value.length;

          const percent = total
            ? Math.min(
                100,
                Math.round(
                  (received / total) * 100
                )
              )
            : 0;

          progressBar.style.width =
            `${percent}%`;

          progressText.textContent =
            `${percent}%`;
        }

        const blob = new Blob(
          chunks,
          {
            type:
              'application/octet-stream',
          }
        );

        const objectUrl =
          URL.createObjectURL(blob);

        const anchor =
          document.createElement('a');

        anchor.href = objectUrl;

        anchor.download =
          metadata.original_name;

        document.body.appendChild(
          anchor
        );

        anchor.click();

        anchor.remove();

        URL.revokeObjectURL(
          objectUrl
        );

        progressBar.style.width =
          '100%';

        progressText.textContent =
          '100%';

        toast(
          'Download complete.'
        );
      } catch (error) {
        codeInput.classList.add(
          'error'
        );

        toast(
          error.message,
          'error'
        );
      } finally {
        setButtonLoading(
          submitButton,
          false
        );
      }
    }
  );
}

document.addEventListener('DOMContentLoaded', () => {
  refreshAuthStatus();
  bindAuthForm();
  setupUploadPage();
  setupDownloadPage();
  setupFilesPage();
});