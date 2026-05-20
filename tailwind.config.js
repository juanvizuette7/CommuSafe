module.exports = {
  content: ["./frontend/templates/**/*.html"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      colors: {
        primary: "#1A1A2E",
        secondary: "#16213E",
        accent: "#0F3460",
        danger: "#E94560",
        success: "#10B981",
        surface: "#F8FAFC",
        slatepanel: "#0F172A",
      },
      boxShadow: {
        soft: "0 18px 45px rgba(15, 23, 42, 0.08)",
        glass: "0 20px 60px rgba(15, 52, 96, 0.15)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
    },
  },
};
