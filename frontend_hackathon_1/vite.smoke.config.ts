// Temporary: used only for isolated browser verification, deleted before commit.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5184,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:5099" },
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
