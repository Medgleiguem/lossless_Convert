/**
 * components/InfoGrid.jsx
 * -----------------------
 * "How it works" info cards shown at the bottom of the page.
 */

import React from 'react';

const INFO_CARDS = [
  {
    icon:  '🎵→🖼️',
    title: 'MP3 → PNG (lossless)',
    text:  'Every byte of the audio is packed into RGB pixel values. Decode it back to get the bit-perfect original.',
  },
  {
    icon:  '🖼️→🎵',
    title: 'PNG → MP3 (lossless)',
    text:  'The PNG pixel data is unpacked back to bytes. A CRC-32 checksum guarantees nothing changed.',
  },
  {
    icon:  '🕵️',
    title: 'Hide image in MP3',
    text:  'Your image is appended after the last MP3 audio frame. Players only read frames — the image is invisible to them.',
  },
  {
    icon:  '🔒',
    title: 'Always verified',
    text:  'Both codecs embed a CRC-32 checksum. Decoding fails loudly if even one byte was corrupted.',
  },
];

export function InfoGrid() {
  return (
    <div className="grid grid-cols-2 gap-px mt-14 border border-border rounded-xl overflow-hidden animate-fade-up sm:grid-cols-4">
      {INFO_CARDS.map(({ icon, title, text }) => (
        <div key={title} className="p-5 bg-surface hover:bg-surface2 transition-colors">
          <div className="text-xl mb-3">{icon}</div>
          <p className="font-display font-bold text-[11px] uppercase tracking-wide text-accent mb-2">
            {title}
          </p>
          <p className="text-[11px] text-muted2 leading-relaxed">{text}</p>
        </div>
      ))}
    </div>
  );
}