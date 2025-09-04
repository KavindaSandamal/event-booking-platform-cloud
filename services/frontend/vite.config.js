import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    allowedHosts: [
      'event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com',
      'localhost',
      '127.0.0.1'
    ],
    hmr: false,
    strictPort: true
  },
  resolve: {
    dedupe: ['react', 'react-dom']
  }
})
