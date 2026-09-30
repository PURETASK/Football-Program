import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8080';

function rootRedirect() {
  return {
    name: 'root-redirect',
    configureServer(server: { middlewares: { use: (middleware: any) => void } }) {
      server.middlewares.use((req: any, res: any, next: any) => {
        if (req.url === '/' || req.url === '') {
          res.writeHead(302, { Location: '/app/' });
          res.end();
          return;
        }
        next();
      });
    },
  };
}

export default defineConfig({
  base: '/app/',
  plugins: [react(), rootRedirect()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/health': { target: apiTarget, changeOrigin: true },
      '/v1': { target: apiTarget, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    globals: true,
    // Workspace route tests mount lazy React trees and share the jsdom global.
    // Keep files isolated at the runner level so parallel module loading
    // cannot make one route's async render satisfy another route's assertion.
    fileParallelism: false,
  },
});
