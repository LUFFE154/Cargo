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
    const json = atob(payload.replaceAll('-', '+').replaceAll('_', '/'));
    return JSON.parse(
      decodeURIComponent(
        Array.from(json, (char) => `%${char.codePointAt(0).toString(16).padStart(2, '0')}`).join('')
      )
    );
  } catch {
    return null;
  }
}

function toast(message, kind = 'success') {
  const host = $('toastHost');
  const node = document.createElement('div');
  node.className = `toast ${kind}`;
  node.textContent = message;
  host.appendChild(node);
  window.setTimeout(() => node.remove(), 4600);
}

function refreshAuthStatus() {
  const status = $('authStatus');
  const token = getToken();
  if (!status) return;
  if (!token) {
    status.textContent = 'Not signed in';
    return;
  }
  const payload = decodeJwtPayload(token);
  status.textContent = payload?.email ? `Signed in as ${payload.email}` : 'Signed in';
}

async function submitAuth(form, mode) {
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  const response = await fetch(`${API_PREFIX}/auth/${mode}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Authentication failed');
  }
  return response.json();
}

function bindAuthForm() {
  const form = $('authForm');
  const registerButton = $('registerButton');
  if (!form || !registerButton) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const result = await submitAuth(form, 'login');
      setToken(result.access_token);
      toast('Signed in successfully.');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      button.disabled = false;
    }
  });

  registerButton.addEventListener('click', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const result = await submitAuth(form, 'register');
      setToken(result.access_token);
      toast('Account created and signed in.');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      button.disabled = false;
    }
  });
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

  if (!form || !dropZone || !fileInput) return;

  dropZone.addEventListener('click', () => fileInput.click());
  ['dragenter', 'dragover'].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropZone.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });
  dropZone.addEventListener('drop', (event) => {
    const dataTransfer = new DataTransfer();
    Array.from(event.dataTransfer.files).forEach((file) => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
    toast(`${fileInput.files[0]?.name || 'File'} selected.`);
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) toast(`${fileInput.files[0].name} selected.`);
  });

  copyButton.addEventListener('click', async () => {
    await navigator.clipboard.writeText(transferCode.textContent.trim());
    toast('Transfer code copied.');
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) {
      toast('Choose a file first.', 'error');
      return;
    }
    const token = getToken();
    if (!token) {
      toast('Sign in before uploading.', 'error');
      return;
    }

    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('expires_in_seconds', $('expiresInSeconds').value || '3600');

    xhr.open('POST', `${API_PREFIX}/transfers`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const percent = Math.round((event.loaded / event.total) * 100);
      progressBar.style.width = `${percent}%`;
      progressText.textContent = `${percent}%`;
    };
    xhr.onload = () => {
      if (xhr.status < 200 || xhr.status >= 300) {
        toast('Upload failed.', 'error');
        return;
      }
      const result = JSON.parse(xhr.responseText);
      transferCode.textContent = result.transfer_code;
      resultHint.textContent = `Uploaded ${result.original_name}. Share this code with the other device.`;
      copyButton.disabled = false;
      downloadLink.href = `${API_PREFIX}/transfers/${result.transfer_code}/download`;
      downloadLink.setAttribute('aria-disabled', 'false');
      qrCodeImage.src = `${API_PREFIX}/transfers/${result.transfer_code}/qr.png`;
      progressBar.style.width = '100%';
      progressText.textContent = '100%';
      toast('Transfer created successfully.');
    };
    xhr.onerror = () => toast('Upload failed.', 'error');
    xhr.send(formData);
  });
}

function setupDownloadPage() {
  const form = $('downloadForm');
  const progressBar = $('downloadProgressBar');
  const progressText = $('downloadProgressText');
  const infoName = $('downloadFileName');
  const infoSize = $('downloadFileSize');
  const infoStatus = $('downloadFileStatus');

  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const code = $('downloadCode').value.trim().toUpperCase();
    if (code.length !== 6) {
      toast('Enter a 6-character transfer code.', 'error');
      return;
    }

    try {
      const metadataResponse = await fetch(`${API_PREFIX}/transfers/${code}`);
      if (!metadataResponse.ok) throw new Error('Transfer code not found');
      const metadata = await metadataResponse.json();
      infoName.textContent = metadata.original_name;
      infoSize.textContent = `${(metadata.size_bytes / (1024 * 1024)).toFixed(2)} MB`;
      infoStatus.textContent = metadata.status;

      const response = await fetch(`${API_PREFIX}/transfers/${code}/download`);
      if (!response.ok || !response.body) throw new Error('Download failed');

      const total = Number(response.headers.get('content-length') || metadata.size_bytes || '0');
      const reader = response.body.getReader();
      const chunks = [];
      let received = 0;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        received += value.length;
        const percent = total ? Math.min(100, Math.round((received / total) * 100)) : 0;
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${percent}%`;
      }

      const blob = new Blob(chunks, { type: 'application/octet-stream' });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = metadata.original_name;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
      progressBar.style.width = '100%';
      progressText.textContent = '100%';
      toast('Download complete.');
    } catch (error) {
      toast(error.message, 'error');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  refreshAuthStatus();
  bindAuthForm();
  setupUploadPage();
  setupDownloadPage();
});
