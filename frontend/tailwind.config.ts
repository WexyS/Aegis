import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/layouts/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#050814",
        foreground: "#F8FAFC",
        surface: {
          DEFAULT: "rgba(12, 18, 31, 0.78)",
          secondary: "rgba(18, 27, 43, 0.72)",
          highlight: "rgba(36, 48, 68, 0.54)",
        },
        accent: {
          DEFAULT: "#06b6d4",
          light: "#22d3ee",
          glow: "rgba(6, 182, 212, 0.3)",
        },
        secondary: {
          DEFAULT: "#8b5cf6",
          light: "#a78bfa",
          glow: "rgba(139, 92, 246, 0.3)",
        },
        danger: "#f43f5e",
        success: "#10b981",
        warning: "#f59e0b",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "scanline": "scanline 4s linear infinite",
        "spin-slow": "spin 8s linear infinite",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite alternate",
      },
      keyframes: {
        scanline: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        "glow-pulse": {
          "0%": { opacity: "0.5", filter: "brightness(1)" },
          "100%": { opacity: "1", filter: "brightness(1.2)" },
        }
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
