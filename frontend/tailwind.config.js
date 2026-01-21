/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vvlive-dark': '#1a1a1a',
        'vvlive-primary': '#3b82f6',
        'vvlive-success': '#10b981',
        'vvlive-warning': '#f59e0b',
        'vvlive-danger': '#ef4444',
      }
    },
  },
  plugins: [],
}