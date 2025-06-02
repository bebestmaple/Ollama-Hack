import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  build: {
    chunkSizeWarningLimit: 700, // 适当提高警告阈值
    rollupOptions: {
      output: {
        manualChunks: {
          // React 核心库
          "react-core": ["react", "react-dom", "react-router-dom"],

          // UI 组件库
          "ui-components": [
            "@heroui/number-input",
            "@heroui/button",
            "@heroui/card",
            "@heroui/input",
            "@heroui/modal",
            "@heroui/navbar",
            "@heroui/table",
            "@heroui/tabs",
            "@heroui/toast",
            "@heroui/switch",
            "@heroui/system",
            "@heroui/link",
            "@heroui/dropdown",
            "@heroui/code",
            "@heroui/avatar",
            "@heroui/autocomplete",
            "@heroui/snippet",
            "@heroui/pagination",
            "@heroui/use-theme",
            "@heroui/drawer",
            "@heroui/form",
            "@heroui/checkbox",
            "@heroui/tooltip",
            "@heroui/progress",
            "@heroui/select",
            "@heroui/chip",
          ],

          "ui-support": ["@heroui/theme", "framer-motion", "tailwind-variants"],

          // 图表相关库
          charts: ["apexcharts", "react-apexcharts"],

          // 工具库
          utils: [
            "axios",
            "date-fns",
            "clsx",
            "jwt-decode",
            "@tanstack/react-query",
            "react-hook-form",
            "react-syntax-highlighter",
          ],

          // 图标库
          icons: [
            "@fortawesome/fontawesome-svg-core",
            "@fortawesome/free-regular-svg-icons",
            "@fortawesome/free-solid-svg-icons",
            "@fortawesome/react-fontawesome",
          ],
        },
      },
    },
  },
});
