/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50:  "#FDFCF9",   // lightest — main background
          100: "#F7F4EE",   // card background
          200: "#EDE8DE",   // border color
          300: "#DDD6C8",   // stronger border / dividers
          400: "#C4BAA8",   // muted elements
        },
        ink: {
          900: "#0D0D0D",   // primary text — near black
          800: "#1A1A1A",   // headings
          700: "#2C2C2C",   // secondary text
          600: "#4A4A4A",   // muted text
          500: "#6B6B6B",   // placeholder text
          400: "#8C8C8C",   // very muted
        },
        accent: {
          900: "#1A1208",   // darkest accent
          800: "#2D1F0A",   // dark warm brown
          700: "#5C3D11",   // medium warm brown
          600: "#8B5E1A",   // accent brown
        }
      },
      fontFamily: {
        serif: ["'Playfair Display'", "Georgia", "serif"],
        sans:  ["Inter", "system-ui", "sans-serif"],
        mono:  ["'JetBrains Mono'", "monospace"],
      },
      letterSpacing: {
        widest2: "0.2em",
        widest3: "0.3em",
      }
    },
  },
  plugins: [],
}