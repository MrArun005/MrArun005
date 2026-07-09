import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@game": fileURLToPath(new URL("./src/game", import.meta.url)),
      "@ui": fileURLToPath(new URL("./src/ui", import.meta.url)),
      "@state": fileURLToPath(new URL("./src/state", import.meta.url)),
    },
  },
  server: { port: 5173 },
  build: { target: "es2022", sourcemap: true },
});
