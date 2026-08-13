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

        // Group accent colors — 7 groups, used directly for tab/border/badge
        // backgrounds (no separate darker "solid" accent — text color is
        // chosen per-swatch instead, see tab_badge_text_class in
        // custom_tags.py, to keep contrast readable).
        "tab-badge-0": "#65ccb8",
        "tab-badge-1": "#57ba98",
        "tab-badge-2": "#3b945e",
        "tab-badge-3": "#31708e",
        "tab-badge-4": "#5085a5",
        "tab-badge-5": "#8fc1e3",
        "tab-badge-6": "#3aafa9",
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
      "border-tab-badge-0", "border-tab-badge-1", "border-tab-badge-2", "border-tab-badge-3", "border-tab-badge-4", "border-tab-badge-5", "border-tab-badge-6",
      "border-l-tab-badge-0", "border-l-tab-badge-1", "border-l-tab-badge-2", "border-l-tab-badge-3", "border-l-tab-badge-4", "border-l-tab-badge-5", "border-l-tab-badge-6",
      "border-b-tab-badge-0", "border-b-tab-badge-1", "border-b-tab-badge-2", "border-b-tab-badge-3", "border-b-tab-badge-4", "border-b-tab-badge-5", "border-b-tab-badge-6",
      // Group nav column count (2-7) — built from a Django filter
      // (custom_tags.group_nav_sm_cols), so Tailwind can't see it statically.
      "sm:grid-cols-2", "sm:grid-cols-3", "sm:grid-cols-4", "sm:grid-cols-5", "sm:grid-cols-6", "sm:grid-cols-7",
    ],
  plugins: [],
};
