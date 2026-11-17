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
    },
  },
  plugins: [],
};
export default config;
