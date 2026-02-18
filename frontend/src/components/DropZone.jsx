/**
 * components/DropZone.jsx
 * -----------------------
 * Reusable drag-and-drop file upload zone.
 *
 * Props:
 *   label       - main heading text
 *   hint        - small helper text below label
 *   emoji       - icon emoji shown in the box
 *   isDragOver  - boolean from useDropZone hook
 *   dropZoneProps - event handlers from useDropZone hook
 *   inputProps  - input props from useDropZone hook
 *   file        - currently selected File object (or null)
 *   onClear     - called when user clicks ✕ on the file chip
 */

import React from 'react';
import { formatBytes, fileEmoji } from '../utils/format';

export function DropZone({ label, hint, emoji, isDragOver, dropZoneProps, inputProps, file, onClear }) {
  return (
    <div>
      {/* Drop area */}
      <div
        {...dropZoneProps}
        className={[
          'relative cursor-pointer rounded-lg p-10 text-center transition-all duration-200',
          'border border-dashed',
          isDragOver
            ? 'border-accent bg-accent/5'
            : 'border-border2 bg-surface hover:border-accent hover:bg-accent/[0.02]',
          // Corner marks via pseudo-elements aren't possible with Tailwind inline,
          // so we use a wrapper with a data attribute and target it in CSS
        ].join(' ')}
        data-dropzone
      >
        {/* Corner decorations */}
        <span className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-accent/40" />
        <span className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-accent/40" />

        {/* Icon */}
        <div className="w-11 h-11 mx-auto mb-3 flex items-center justify-center text-xl
                        rounded-xl border border-border2 bg-surface2 transition-all duration-200">
          {emoji}
        </div>

        {/* Text */}
        <p className="font-display font-bold text-sm text-white mb-1">{label}</p>
        <p className="text-xs text-muted leading-relaxed">
          drag &amp; drop or{' '}
          <span
            className="text-accent underline underline-offset-2 cursor-pointer"
            onClick={(e) => { e.stopPropagation(); inputProps.ref?.current?.click(); }}
          >
            browse files
          </span>
          {hint && <><br />{hint}</>}
        </p>

        {/* Hidden file input */}
        <input {...inputProps} />
      </div>

      {/* Selected file chip */}
      {file && (
        <div className="flex items-center gap-3 mt-2 px-3 py-2.5
                        bg-surface2 border border-border2 rounded-md">
          <div className="w-8 h-8 flex items-center justify-center text-sm
                          bg-accent/10 rounded-md flex-shrink-0">
            {fileEmoji(file.name)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-white truncate">{file.name}</p>
            <p className="text-[10px] text-muted mt-0.5">{formatBytes(file.size)}</p>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="text-muted hover:text-error text-sm leading-none px-1 transition-colors"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}