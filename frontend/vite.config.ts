import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8080';

export default defineConfig({
  base: '/app/',
  plugins: [react()],
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
      '/health': apiTarget,
      '/v1': apiTarget,
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
