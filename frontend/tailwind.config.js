/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono:    ['"Space Mono"', 'monospace'],
        display: ['"Unbounded"', 'sans-serif'],
      },
      colors: {
        bg:       '#080810',
        surface:  '#0e0e1a',
        surface2: '#141428',
        border:   '#1c1c36',
        border2:  '#262640',
        accent:   '#00e5ff',
        accent2:  '#aaff00',
        muted:    '#4a4a6a',
        muted2:   '#6a6a9a',
        success:  '#00e5a0',
        error:    '#ff3d71',
      },
      animation: {
        'fade-up': 'fadeUp 0.5s ease both',
        'pulse-dot': 'pulseDot 2s ease-in-out infinite',
        'scan': 'scan 7s linear infinite',
        'glow': 'glow 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeUp:   { from: { opacity:'0', transform:'translateY(16px)' }, to: { opacity:'1', transform:'translateY(0)' } },
        pulseDot: { '0%,100%': { opacity:'1' }, '50%': { opacity:'0.3' } },
        scan:     { '0%': { transform:'translateY(-100%)' }, '100%': { transform:'translateY(100vh)' } },
        glow:     { '0%,100%': { boxShadow:'0 0 4px #00e5ff' }, '50%': { boxShadow:'0 0 18px #00e5ff, 0 0 36px #00e5ff' } },
      },
    }
  },
  plugins: [],
}
