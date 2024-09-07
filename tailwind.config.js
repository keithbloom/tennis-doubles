/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./tournament/templates/**/*.html", "./tournament/static/**/*.js"],
  theme: {
    extend: {
      colors: {
        "custom-teal": "#09c3a1",
        "custom-green": "#91c768",
        "custom-lime": "#c0dd55",
        "custom-yellow": "#eaf3a5",
        "custom-gray": "#f2f2f2",
        "custom-pink-0": "#ffc983",
        "custom-pink-1": "#ffe6ed",
        "custom-pink-2": "#f283c6",
        "custom-pink-3": "#f47c71",
        "custom-pink-4": "#ff4d85",
        "custom-pink-5": "#f36059",
        "custom-pink-6": "#f05c77",
      },
      fontFamily: {
        cowboys: ["Cowboys", "sans-serif"],
      },
    },
  },
  safelist: [
    "bg-custom-pink-0",
    "bg-custom-pink-1",
    "bg-custom-pink-2",
    "bg-custom-pink-3",
    "bg-custom-pink-4",
    "bg-custom-pink-5",
    "bg-custom-pink-6",
  ],
  plugins: [],
};
