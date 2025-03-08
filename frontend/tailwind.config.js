/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        input: {
          text: '#333333',
          background: '#ffffff',
          border: '#d1d5db',
          focus: '#3b82f6',
        }
      }
    },
  },
  plugins: [],
} 