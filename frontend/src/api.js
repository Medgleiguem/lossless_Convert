/**
 * api.js — All HTTP calls to the Flask backend.
 * Each exported function maps 1-to-1 to one backend endpoint.
 */

const BASE_URL = process.env.REACT_APP_API_URL || '';

// ── Internal XHR helper ───────────────────────────────────────────────────────

/** Upload FormData via XHR; supports upload-progress reporting. */
function uploadRequest(endpoint, formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 75));
    };

    xhr.onload = () => {
      onProgress?.(100);
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve({ blob: xhr.response, getHeader: (n) => xhr.getResponseHeader(n) || '' });
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        try   { reject(new Error(JSON.parse(reader.result).error || `Server error ${xhr.status}`)); }
        catch { reject(new Error(`Server error ${xhr.status}`)); }
      };
      reader.onerror = () => reject(new Error(`Server error ${xhr.status}`));
      reader.readAsText(xhr.response);
    };

    xhr.onerror   = () => reject(new Error('Network error — is the Flask server running on port 5000?'));
    xhr.ontimeout = () => reject(new Error('Request timed out after 3 minutes.'));
    xhr.timeout   = 180_000;
    xhr.responseType = 'blob';
    xhr.open('POST', `${BASE_URL}${endpoint}`);
    xhr.send(formData);
  });
}

function filenameFrom(header) {
  const m = header.match(/filename="([^"]+)"/);
  return m ? m[1] : null;
}

// ── PNG Codec ─────────────────────────────────────────────────────────────────

/** Encode any file → SoundPixel PNG. */
export async function pngEncode(file, onProgress) {
  const form = new FormData();
  form.append('file', file);
  const { blob, getHeader } = await uploadRequest('/api/png/encode', form, onProgress);
  return {
    blob,
    filename:   filenameFrom(getHeader('Content-Disposition')) ?? 'soundpixel.png',
    width:      parseInt(getHeader('X-Image-Width'),  10) || 0,
    height:     parseInt(getHeader('X-Image-Height'), 10) || 0,
    inputSize:  parseInt(getHeader('X-Input-Size'),   10) || 0,
    outputSize: parseInt(getHeader('X-Output-Size'),  10) || 0,
  };
}

/** Decode SoundPixel PNG → original file. */
export async function pngDecode(file, onProgress) {
  const form = new FormData();
  form.append('file', file);
  const { blob, getHeader } = await uploadRequest('/api/png/decode', form, onProgress);
  return {
    blob,
    filename:   filenameFrom(getHeader('Content-Disposition')) ?? getHeader('X-Original-Filename') ?? 'decoded',
    outputSize: parseInt(getHeader('X-Output-Size'), 10) || 0,
  };
}

// ── MP3 Steganography Codec ───────────────────────────────────────────────────

/** Embed an image inside an MP3 (MP3 still plays normally). */
export async function mp3Encode(mp3File, imageFile, onProgress) {
  const form = new FormData();
  form.append('mp3',   mp3File);
  form.append('image', imageFile);
  const { blob, getHeader } = await uploadRequest('/api/mp3/encode', form, onProgress);
  return {
    blob,
    filename:  filenameFrom(getHeader('Content-Disposition')) ?? 'soundpixel.mp3',
    mp3Size:   parseInt(getHeader('X-Mp3-Size'),   10) || 0,
    imageSize: parseInt(getHeader('X-Image-Size'), 10) || 0,
    totalSize: parseInt(getHeader('X-Total-Size'), 10) || 0,
  };
}

/** Extract the image hidden inside a SoundPixel MP3. */
export async function mp3Decode(file, onProgress) {
  const form = new FormData();
  form.append('file', file);
  const { blob, getHeader } = await uploadRequest('/api/mp3/decode', form, onProgress);
  return {
    blob,
    filename:   filenameFrom(getHeader('Content-Disposition')) ?? getHeader('X-Original-Filename') ?? 'decoded.png',
    outputSize: parseInt(getHeader('X-Output-Size'), 10) || 0,
  };
}