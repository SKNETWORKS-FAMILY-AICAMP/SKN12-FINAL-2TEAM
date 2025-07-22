import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      /* ① 다크·라이트별 prose 기본 색상 */
      typography: ({ theme }: { theme: any }) => ({
        DEFAULT: { css: { color: theme("colors.gray.800") } },
        invert: { css: { color: theme("colors.gray.100") } },
      }),

      /* ② (선택) 프로젝트 컬러 팔레트 예시 */
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        /* … 나머지 색상은 기존 그대로 … */
      },

      /* ③ 이미 쓰고 있던 radius · keyframes 유지 */
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  /* ④ 플러그인에 typography 추가 */
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
};

export default config;
