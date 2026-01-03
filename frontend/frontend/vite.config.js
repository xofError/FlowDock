// vite.config.js (or .mjs)
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite'; // <-- Import the plugin


export default defineConfig({
  plugins: [
    react(),
    tailwindcss() 
  ],
  server: {
    host: true, // Needed for Docker
    port: 5173,
    proxy: {
      // Proxy API requests to the Gateway (or Auth/Media services directly)
      '/api': {
        target: 'http://localhost:80', // Point this to your Nginx Gateway Port
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: 'http://localhost:80', // Point this to your Nginx Gateway Port
        changeOrigin: true,
        secure: false,
      }
    }
  }
});