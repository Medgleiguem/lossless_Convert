/**
 * utils/format.js
 * ---------------
 * Pure utility functions — no side effects, no imports.
 */

/** Format raw bytes into a human-readable string. */
export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '—';
  if (bytes < 1_024)         return `${bytes} B`;
  if (bytes < 1_048_576)     return `${(bytes / 1_024).toFixed(1)} KB`;
  return `${(bytes / 1_048_576).toFixed(2)} MB`;
}

/** Return an emoji that represents a file by its extension. */
export function fileEmoji(filename = '') {
  const ext = filename.split('.').pop().toLowerCase();
  const map = {
    mp3: '🎵', wav: '🔊', flac: '🎼', ogg: '🎶', aac: '🎧', m4a: '🎵', opus: '🎵',
    png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', webp: '🖼️', bmp: '🖼️', tiff: '🖼️',
    pdf: '📄', zip: '📦', mp4: '🎬',
  };
  return map[ext] ?? '📁';
}

/** True if the filename has an image extension. */
export function isImageFile(filename = '') {
  const ext = filename.split('.').pop().toLowerCase();
  return ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff'].includes(ext);
}

/** True if the filename has an audio extension. */
export function isAudioFile(filename = '') {
  const ext = filename.split('.').pop().toLowerCase();
  return ['mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a', 'opus', 'aiff'].includes(ext);
}