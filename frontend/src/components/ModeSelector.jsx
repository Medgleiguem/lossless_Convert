/**
 * components/ModeSelector.jsx
 * ---------------------------
 * 4-card grid for selecting which conversion mode to use.
 */

import React from 'react';

const MODES = [
  {
    id:          'png-encode',
    emoji:       '🎵',
    title:       'MP3 → PNG',
    description: 'Turn any audio file into a lossless PNG image',
    badge:       'PNG Codec',
    badgeColor:  'text-accent border-accent/30 bg-accent/5',
  },
  {
    id:          'png-decode',
    emoji:       '🔄',
    title:       'PNG → MP3',
    description: 'Recover the original audio from a SoundPixel PNG',
    badge:       'PNG Codec',
    badgeColor:  'text-accent border-accent/30 bg-accent/5',
  },
  {
    id:          'mp3-encode',
    emoji:       '🕵️',
    title:       'Hide Image in MP3',
    description: 'Embed an image inside an MP3 — audio still plays normally',
    badge:       'Steganography',
    badgeColor:  'text-accent2 border-accent2/30 bg-accent2/5',
  },
  {
    id:          'mp3-decode',
    emoji:       '🖼️',
    title:       'Extract Image from MP3',
    description: 'Pull out the image hidden inside a SoundPixel MP3',
    badge:       'Steganography',
    badgeColor:  'text-accent2 border-accent2/30 bg-accent2/5',
  },
];

export { MODES };

/**
 * Props:
 *   activeMode  - currently selected mode id
 *   onSelect    - called with the mode id when user clicks a card
 */
export function ModeSelector({ activeMode, onSelect }) {
  return (
    <div className="grid grid-cols-2 gap-3 mt-10 mb-8 animate-fade-up sm:grid-cols-2">
      {MODES.map((mode) => {
        const isActive = activeMode === mode.id;
        return (
          <button
            key={mode.id}
            onClick={() => onSelect(mode.id)}
            className={[
              'flex items-start gap-3 p-4 rounded-lg border text-left transition-all duration-200',
              isActive
                ? 'border-accent bg-accent/[0.07]'
                : 'border-border2 bg-surface hover:border-accent/50 hover:bg-surface2',
            ].join(' ')}
          >
            {/* Icon */}
            <div className={[
              'w-9 h-9 flex items-center justify-center text-lg rounded-lg flex-shrink-0 transition-colors',
              isActive ? 'bg-accent/15' : 'bg-surface2',
            ].join(' ')}>
              {mode.emoji}
            </div>

            {/* Text */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className={[
                  'font-display font-bold text-xs',
                  isActive ? 'text-accent' : 'text-white',
                ].join(' ')}>
                  {mode.title}
                </span>
                <span className={`text-[9px] border rounded px-1.5 py-0.5 uppercase tracking-wider ${mode.badgeColor}`}>
                  {mode.badge}
                </span>
              </div>
              <p className="text-[11px] text-muted leading-snug">{mode.description}</p>
            </div>

            {/* Active dot */}
            <div className={[
              'w-2 h-2 rounded-full mt-1 flex-shrink-0 transition-all',
              isActive ? 'bg-accent' : 'border border-border2',
            ].join(' ')} />
          </button>
        );
      })}
    </div>
  );
}