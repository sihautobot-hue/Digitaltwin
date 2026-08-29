/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        scada: {
          bg: '#121212',
          surface: '#181818',
          card: '#1E1E1E',
          cardHover: '#252525',
          border: '#2A2A2A',
          borderLight: '#3A3A3A',
          muted: '#8E8E93',
          subtle: '#636366',
          highlight: '#2C2C2E',
          cyan: '#00E5FF',
          blue: '#2F80ED',
          amber: '#FFB800',
          red: '#FF3344',
          green: '#00FF66',
          ice: '#A5F3FC',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Roboto Mono"', 'Consolas', 'monospace'],
        display: ['"Space Grotesk"', 'Inter', 'sans-serif']
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'radar-sweep': 'sweep 4s linear infinite',
        'beacon': 'beacon 2s ease-in-out infinite',
      },
      keyframes: {
        sweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        beacon: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.4', transform: 'scale(1.15)' },
        }
      },
      boxShadow: {
        'scada-glow': '0 0 15px rgba(0, 229, 255, 0.15)',
        'scada-green': '0 0 12px rgba(34, 197, 94, 0.25)',
        'scada-yellow': '0 0 12px rgba(234, 179, 8, 0.25)',
        'scada-red': '0 0 15px rgba(239, 68, 68, 0.35)',
      }
    },
  },
  plugins: [],
}
