const BASE = process.env.REACT_APP_API_URL || '';

/**
 * @param {File} file
 * @param {(pct: number) => void} onProgress
 * @returns {Promise<{ blob: Blob, filename: string, width: number, height: number, originalSize: number }>}
 */
export async function encodeAudio(file, onProgress) {
  const form = new FormData();
  form.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 60));
    };

    xhr.onload = () => {
      onProgress?.(100);
      if (xhr.status >= 200 && xhr.status < 300) {
        const cd = xhr.getResponseHeader('Content-Disposition') || '';
        const match = cd.match(/filename="([^"]+)"/);
        const filename = match ? match[1] : 'output_soundpixel.png';
        const width = parseInt(xhr.getResponseHeader('X-Image-Width') || '0', 10);
        const height = parseInt(xhr.getResponseHeader('X-Image-Height') || '0', 10);
        const originalSize = parseInt(xhr.getResponseHeader('X-Original-Size') || '0', 10);
        resolve({ blob: xhr.response, filename, width, height, originalSize });
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.error || `Server error ${xhr.status}`));
        } catch {
          reject(new Error(`Server error ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error('Network error — is the server running?'));
    xhr.ontimeout = () => reject(new Error('Request timed out.'));
    xhr.timeout = 120_000;

    xhr.open('POST', `${BASE}/api/encode`);
    xhr.responseType = 'blob';
    xhr.send(form);
  });
}

/**
 * @param {File} file
 * @param {(pct: number) => void} onProgress
 * @returns {Promise<{ blob: Blob, filename: string, decodedSize: number }>}
 */
export async function decodeImage(file, onProgress) {
  const form = new FormData();
  form.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 60));
    };

    xhr.onload = () => {
      onProgress?.(100);
      if (xhr.status >= 200 && xhr.status < 300) {
        const cd = xhr.getResponseHeader('Content-Disposition') || '';
        const match = cd.match(/filename="([^"]+)"/);
        const filename = match ? match[1] : 'decoded_audio.mp3';
        const decodedSize = parseInt(xhr.getResponseHeader('X-Decoded-Size') || '0', 10);
        resolve({ blob: xhr.response, filename, decodedSize });
      } else {
        try {
          const reader = new FileReader();
          reader.onload = () => {
            const err = JSON.parse(reader.result);
            reject(new Error(err.error || `Server error ${xhr.status}`));
          };
          reader.readAsText(xhr.response);
        } catch {
          reject(new Error(`Server error ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error('Network error — is the server running?'));
    xhr.ontimeout = () => reject(new Error('Request timed out.'));
    xhr.timeout = 120_000;

    xhr.open('POST', `${BASE}/api/decode`);
    xhr.responseType = 'blob';
    xhr.send(form);
  });
}
