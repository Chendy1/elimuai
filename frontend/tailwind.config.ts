import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: "#174C3C",
        deep: "#10392E",
        ivory: "#FAF8F1",
        sage: "#E5EEE8",
        gold: "#D5AE62",
        ink: "#202B27",
        muted: "#68746D",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "Segoe UI", "sans-serif"],
      },
      boxShadow: { card: "0 1px 2px rgba(16,57,46,0.06), 0 4px 16px rgba(16,57,46,0.06)" },
    },
  },
  plugins: [],
};
export default config;
