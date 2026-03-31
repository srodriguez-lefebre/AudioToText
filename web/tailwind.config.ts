import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#0a0a0a",
          surface: "#141414",
          border: "#262626",
          text: "#e5e5e5",
          muted: "#a3a3a3",
          accent: "#3b82f6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
