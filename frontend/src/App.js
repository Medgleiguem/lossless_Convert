/**
 * App.js
 * ------
 * Root component. Manages which conversion mode is active and renders
 * the appropriate page component. All conversion logic lives in the pages.
 */

import React, { useState } from "react";
import { ModeSelector } from "./components/ModeSelector";
import { InfoGrid } from "./components/InfoGrid";
import { PngEncodePage } from "./pages/PngEncodePage";
import { PngDecodePage } from "./pages/PngDecodePage";
import { Mp3EncodePage } from "./pages/Mp3EncodePage";
import { Mp3DecodePage } from "./pages/Mp3DecodePage";

// Map each mode ID to the component that handles it
const PAGE_MAP = {
  "png-encode": PngEncodePage,
  "png-decode": PngDecodePage,
  "mp3-encode": Mp3EncodePage,
  "mp3-decode": Mp3DecodePage,
};

export default function App() {
  const [activeMode, setActiveMode] = useState("png-encode");

  // When the mode changes, reset by re-mounting via key change
  const [pageKey, setPageKey] = useState(0);

  const handleModeSelect = (modeId) => {
    setActiveMode(modeId);
    setPageKey((k) => k + 1); // re-mount the page to clear all state
  };

  const ActivePage = PAGE_MAP[activeMode];

  return (
    <div className="relative z-10 max-w-3xl mx-auto px-6 py-14 pb-24">
      {/* ── Header ── */}
      <header className="mb-0">
        {/* Live indicator */}
        <div
          className="inline-flex items-center gap-2 text-[10px] tracking-[0.25em] uppercase
                        text-accent border border-accent/30 px-3.5 py-1.5 mb-5 animate-fade-up"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-dot" />
          Lossless Codec — v2.0
        </div>

        <h1
          className="font-display font-Black text-5xl sm:text-6xl leading-none
             tracking-tight mb-3 animate-fade-up"
          style={{ animationDelay: "80ms" }}
        >
          <span className="text-green-500">Sound</span>
          <span className="text-accent">Pixel</span>
        </h1>

        <p
          className="text-xs text-muted2 tracking-wide leading-7 max-w-lg animate-fade-up"
          style={{ animationDelay: "160ms" }}
        >
          Four conversion modes. Two codecs. Every byte preserved. CRC-32
          verified on every decode.
        </p>
      </header>

      {/* ── Mode selector ── */}
      <ModeSelector activeMode={activeMode} onSelect={handleModeSelect} />

      {/* ── Section divider ── */}
      <div className="flex items-center gap-3 mb-6">
        <span className="text-[10px] tracking-[0.2em] uppercase text-muted">
          {activeMode.replace("-", " → ").toUpperCase()}
        </span>
        <div className="flex-1 h-px bg-border" />
      </div>

      {/* ── Active page (re-mounts on mode change via key) ── */}
      <ActivePage key={pageKey} />

      {/* ── How it works ── */}
      <InfoGrid />

      {/* ── Footer ── */}
      <footer className="text-center mt-14 text-[10px] text-muted tracking-widest uppercase animate-fade-up">
        SoundPixel v2 · Lossless Audio ↔ PNG · Image ↔ MP3 Steganography ·
        Python + React
      </footer>
    </div>
  );
}
