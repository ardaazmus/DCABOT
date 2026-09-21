import { defineConfig, mergeConfig } from "vite";
import base from "./vite.config";

// TEMPORARY (Faz 15 screenshots only, deleted at session end): same app,
// /api proxy points at the screenshot backend :8001 (current code).
export default mergeConfig(
  base,
  defineConfig({
    server: {
      host: "127.0.0.1",
      port: 5174,
      proxy: { "/api": "http://127.0.0.1:8001" },
    },
  }),
);
