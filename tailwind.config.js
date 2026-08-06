/** @type {import('tailwindcss').Config} */

const colors = require('tailwindcss/colors')
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

        // Group accent colors — 7 groups. Pastel for backgrounds/tab fills,
        // "solid" for borders/active-state accents.
        "tab-badge-0": colors.blue[100],
        "tab-badge-1": colors.rose[100],
        "tab-badge-2": colors.teal[100],
        "tab-badge-3": colors.amber[100],
        "tab-badge-4": colors.violet[100],
        "tab-badge-5": colors.lime[100],
        "tab-badge-6": colors.cyan[100],
        "tab-badge-solid-0": colors.blue[500],
        "tab-badge-solid-1": colors.rose[500],
        "tab-badge-solid-2": colors.teal[500],
        "tab-badge-solid-3": colors.amber[500],
        "tab-badge-solid-4": colors.violet[500],
        "tab-badge-solid-5": colors.lime[600],
        "tab-badge-solid-6": colors.cyan[500],
      },
      fontFamily: {
        monofett: ["Monofett", "sans-serif"],
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
      // Group accent colors (0-6) — every utility variant actually used in
      // templates has to be listed explicitly; Tailwind can't statically see
      // classes built from a Django {{ group_index }} interpolation.
      "bg-tab-badge-0", "bg-tab-badge-1", "bg-tab-badge-2", "bg-tab-badge-3", "bg-tab-badge-4", "bg-tab-badge-5", "bg-tab-badge-6",
      "border-l-tab-badge-0", "border-l-tab-badge-1", "border-l-tab-badge-2", "border-l-tab-badge-3", "border-l-tab-badge-4", "border-l-tab-badge-5", "border-l-tab-badge-6",
      "border-b-tab-badge-0", "border-b-tab-badge-1", "border-b-tab-badge-2", "border-b-tab-badge-3", "border-b-tab-badge-4", "border-b-tab-badge-5", "border-b-tab-badge-6",
      "border-tab-badge-solid-0", "border-tab-badge-solid-1", "border-tab-badge-solid-2", "border-tab-badge-solid-3", "border-tab-badge-solid-4", "border-tab-badge-solid-5", "border-tab-badge-solid-6",
      "border-l-tab-badge-solid-0", "border-l-tab-badge-solid-1", "border-l-tab-badge-solid-2", "border-l-tab-badge-solid-3", "border-l-tab-badge-solid-4", "border-l-tab-badge-solid-5", "border-l-tab-badge-solid-6",
    ],
  plugins: [],
};
