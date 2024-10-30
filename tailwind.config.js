/** @type {import('tailwindcss').Config} */
module.exports = {
  content: {
    relative: true,
    files: [
      './templates/**/*.{html,js}',
    ],
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["aqua", "dark", "light", "cupcake", "synthwave"],
  },
} 