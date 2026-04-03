import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 3001,
    proxy: {
      "/api": {
        target: "http://localhost:8095",
        changeOrigin: true,
      },
    },
  },
});
