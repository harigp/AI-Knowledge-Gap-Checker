/** @type {import('tailwindcss').Config} */

// Violet-blue brand scale (600 is the primary action color).
const violetBlue = {
  50: '#f3f2ff',
  100: '#e9e7ff',
  200: '#d5d1ff',
  300: '#b6adff',
  400: '#9180fc',
  500: '#7457f6',
  600: '#5f3ded',
  700: '#512ed6',
  800: '#4327ad',
  900: '#39258a',
  950: '#22154f',
};

// Cool neutral scale with a faint blue tint; 50 is the cool-white page background.
const coolNeutral = {
  50: '#f7f8fc',
  100: '#eef0f7',
  200: '#e2e5ef',
  300: '#cbd0de',
  400: '#9aa1b5',
  500: '#6b7287',
  600: '#4f566b',
  700: '#3d4356',
  800: '#272c3b',
  900: '#181b26',
  950: '#0e1018',
};

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      // Components use blue/indigo for brand actions and gray/slate for neutrals;
      // remapping them here themes the whole app without touching component classes.
      // Status colors (green/emerald, red, amber) are left as Tailwind defaults.
      colors: {
        blue: violetBlue,
        indigo: violetBlue,
        violet: violetBlue,
        gray: coolNeutral,
        slate: coolNeutral,
      },
      // Terminal-style cursor used in the logo.
      keyframes: {
        blink: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0' } },
      },
      animation: {
        blink: 'blink 1.1s step-end infinite',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
