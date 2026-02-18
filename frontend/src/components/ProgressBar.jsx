/**
 * components/ProgressBar.jsx
 * --------------------------
 * Thin animated progress bar shown during conversion.
 */

import React from 'react';

export function ProgressBar({ percent }) {
  return (
    <div className="h-0.5 bg-border rounded-full overflow-hidden mt-3">
      <div
        className="h-full bg-accent rounded-full transition-all duration-300 ease-out animate-glow"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}