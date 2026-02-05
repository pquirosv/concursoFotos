import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    // Avoid copying static/public into dist; fotos are not used in production.
    copyPublicDir: false,
  },
  server: {
    proxy: {
      '/api': 'http://api:3000',
    },
  },
})
