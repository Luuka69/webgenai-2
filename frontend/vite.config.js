import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_URL || 'http://127.0.0.1:8011'
  return {
    base:'/webgen/',
    plugins: [tailwindcss(),react()],
    server: {
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
        },
      },
    },
  }
})
