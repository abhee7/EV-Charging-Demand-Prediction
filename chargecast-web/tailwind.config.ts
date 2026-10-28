import type { Config } from "tailwindcss";

/**
 * ChargeCast design system.
 * Light theme matched to the "Material" landing-page template: white surfaces,
 * indigo-to-violet gradient accents and Inter typography. Token NAMES are kept
 * from the previous dark theme so every component continues to work unchanged.
 */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#FFFFFF",
        surface: "#FFFFFF",
        elevated: "#F9FAFB",
        grid: "#E5E7EB",
        signal: "#4F46E5",
        prediction: "#EA580C",
        violet: "#7C6CF2",
        rose: "#E11D48",
        lime: "#16A34A",
        ink: "#111827",
        muted: "#6B7280",
        hairline: "rgba(17,24,39,.08)",
        glass: "rgba(17,24,39,.03)",
      },
      fontFamily: {
        display: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
      boxShadow: {
        glass: "0 1px 2px rgba(17,24,39,.04), 0 10px 28px -16px rgba(17,24,39,.14)",
        glow: "0 0 0 1px rgba(79,70,229,.22), 0 0 22px -8px rgba(79,70,229,.45)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        pulse_dot: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
      },
      animation: {
        "fade-up": "fade-up .28s ease-out both",
        "pulse-dot": "pulse_dot 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
