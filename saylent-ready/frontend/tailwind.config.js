/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: '#05070d',
          900: '#0b0f1a',
          850: '#0f1526',
          800: '#131b2e',
          700: '#1c2740',
        },
        accent: {
          cyan: '#22d3ee',
          indigo: '#6366f1',
          amber: '#f59e0b',
          rose: '#f43f5e',
          emerald: '#34d399',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
