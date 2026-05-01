import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

function graphClerkApiProxy(mode: string) {
  const env = loadEnv(mode, process.cwd(), ["GRAPHCLERK_"]);
  const target = env.GRAPHCLERK_API_PROXY_TARGET?.trim() || "http://127.0.0.1:8010";
  return {
    "/api": {
      target,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/api/, ""),
    },
  };
}

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    // Required when `VITE_API_BASE_URL=/api`: otherwise `/api/*` is answered with SPA HTML (200)
    // and `response.json()` fails with "Unexpected token '<'".
    proxy: graphClerkApiProxy(mode),
  },
  preview: {
    // `vite preview` does not use `server`; mirror proxy so production builds work locally.
    proxy: graphClerkApiProxy(mode),
  },
}));
