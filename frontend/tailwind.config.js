/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          navy: {
            DEFAULT: '#0A2540',
            dark: '#061727',
            light: '#143C65',
            muted: '#2A4365',
          },
          gold: {
            DEFAULT: '#D97706',
            dark: '#B45309',
            light: '#F59E0B',
            pale: '#FEF3C7',
          },
          maroon: {
            DEFAULT: '#7F1D1D',
            light: '#991B1B',
          },
          surface: '#F8FAFC',
          border: '#E2E8F0',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
