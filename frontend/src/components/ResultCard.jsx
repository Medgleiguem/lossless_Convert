/**
 * components/ResultCard.jsx
 * -------------------------
 * Displays the conversion result:
 *   - Image preview, audio player, or generic file icon
 *   - Stats row (size, dimensions, etc.)
 *   - Download button
 */

import React from 'react';
import { formatBytes, isImageFile, isAudioFile } from '../utils/format';

// ── Preview variants ──────────────────────────────────────────────────────────

function ImagePreview({ objectUrl, filename }) {
  return (
    <>
      <p className="text-[10px] tracking-widest uppercase text-muted mb-3">Decoded Image</p>
      <img
        src={objectUrl}
        alt={filename}
        className="max-w-full max-h-64 rounded border border-border2"
      />
    </>
  );
}

function AudioPreview({ objectUrl, filename }) {
  return (
    <>
      <p className="font-display font-bold text-sm mb-3">🎵 {filename}</p>
      <audio
        controls
        src={objectUrl}
        className="w-full max-w-sm"
        style={{ filter: 'invert(1) hue-rotate(190deg) saturate(0.6)' }}
      />
    </>
  );
}

function PngPreview({ objectUrl }) {
  return (
    <>
      <p className="text-[10px] tracking-widest uppercase text-muted mb-3">
        SoundPixel PNG — pixel-packed file data
      </p>
      <img
        src={objectUrl}
        alt="Encoded PNG"
        className="max-w-full max-h-64 rounded border border-border2"
        style={{ imageRendering: 'pixelated' }}
      />
    </>
  );
}

function Mp3Preview({ objectUrl }) {
  return (
    <>
      <p className="text-[10px] tracking-widest uppercase text-muted mb-2">
        SoundPixel MP3 — plays as audio, hides your image
      </p>
      <audio
        controls
        src={objectUrl}
        className="w-full max-w-sm"
        style={{ filter: 'invert(1) hue-rotate(190deg) saturate(0.6)' }}
      />
    </>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

/**
 * Props:
 *   result.objectUrl  - blob URL
 *   result.filename   - download filename
 *   result.outputType - 'encoded-png' | 'encoded-mp3' | 'decoded-audio' | 'decoded-image' | 'decoded-file'
 *   result.stats      - { label: value, … }
 */
export function ResultCard({ result }) {
  if (!result) return null;

  const { objectUrl, filename, outputType, stats } = result;

  // Pick the right preview based on what was produced
  const renderPreview = () => {
    switch (outputType) {
      case 'encoded-png':    return <PngPreview   objectUrl={objectUrl} />;
      case 'encoded-mp3':    return <Mp3Preview   objectUrl={objectUrl} />;
      case 'decoded-image':  return <ImagePreview objectUrl={objectUrl} filename={filename} />;
      case 'decoded-audio':  return <AudioPreview objectUrl={objectUrl} filename={filename} />;
      default:
        // Fallback: guess from filename
        if (isImageFile(filename)) return <ImagePreview objectUrl={objectUrl} filename={filename} />;
        if (isAudioFile(filename)) return <AudioPreview objectUrl={objectUrl} filename={filename} />;
        return <p className="text-sm text-muted">📁 {filename}</p>;
    }
  };

  return (
    <div className="mt-7 bg-surface border border-border2 rounded-xl overflow-hidden animate-fade-up">

      {/* Preview area */}
      <div
        className="flex flex-col items-center justify-center p-8 min-h-36 text-center"
        style={{
          background: 'repeating-conic-gradient(#141428 0% 25%, #080810 0% 50%) 0 0 / 20px 20px',
        }}
      >
        {renderPreview()}
      </div>

      {/* Stats + Download */}
      <div className="flex items-center justify-between gap-4 px-5 py-4 border-t border-border flex-wrap">

        {/* Stats */}
        <div className="flex gap-6 flex-wrap">
          {Object.entries(stats).map(([label, value]) => (
            <div key={label}>
              <p className="text-[9px] tracking-widest uppercase text-muted">{label}</p>
              <p className="text-xs font-bold text-white mt-0.5">{formatBytes(value) !== '—' ? value : value}</p>
            </div>
          ))}
        </div>

        {/* Download */}
        <a
          href={objectUrl}
          download={filename}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-md
                     border border-accent text-accent text-[11px] uppercase tracking-widest
                     font-mono transition-all duration-200 hover:bg-accent hover:text-black
                     whitespace-nowrap"
        >
          ↓ Download
        </a>
      </div>
    </div>
  );
}