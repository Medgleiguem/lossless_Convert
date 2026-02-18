/**
 * components/ConvertButton.jsx
 * ----------------------------
 * The primary action button for triggering a conversion.
 */

import React from 'react';

export function ConvertButton({ onClick, disabled, busy, label }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={[
        'block w-full mt-4 py-4 rounded-lg font-display font-bold text-xs tracking-widest uppercase transition-all duration-200',
        disabled
          ? 'bg-surface2 text-muted border border-border2 cursor-not-allowed'
          : 'bg-accent text-black border border-accent cursor-pointer hover:bg-cyan-300 hover:-translate-y-px hover:shadow-[0_6px_20px_rgba(0,229,255,0.22)] active:translate-y-0',
      ].join(' ')}
    >
      {busy ? '⟳ Processing…' : label}
    </button>
  );
}