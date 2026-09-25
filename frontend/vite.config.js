import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { 
    port: 5173, 
    open: false,
    // Libera a URL específica do ngrok ou use ['.ngrok-free.app', '.ngrok-free.dev']
    allowedHosts: ['banter-payable-lumber.ngrok-free.dev', '.ngrok-free.app', '.ngrok-free.dev']
  },
  build: {
    target: 'es2019',
    rollupOptions: {
      output: {
        // separa a biblioteca do codigo da aplicacao para melhorar o cache
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          http: ['axios'],
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.js',
  },
})