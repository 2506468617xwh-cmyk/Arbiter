/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Old names → mapped to new dark theme variables for backward compat
        ink: "var(--ink-primary)",
        muted: "var(--ink-muted)",
        panel: "var(--bg-card)",
        line: "var(--border-card)",
        brand: "var(--accent)",
        // New direct access
        "bg-deep": "var(--bg-deep)",
        "bg-card": "var(--bg-card)",
        "bg-elevated": "var(--bg-elevated)",
        "ink-primary": "var(--ink-primary)",
        "ink-secondary": "var(--ink-secondary)",
        "ink-dim": "var(--ink-dim)",
        accent: "var(--accent)",
        up: "var(--up)",
        down: "var(--down)",
      },
      boxShadow: {
        soft: "var(--shadow-card)",
        glow: "var(--shadow-glow)",
      },
    },
  },
  plugins: [],
};
