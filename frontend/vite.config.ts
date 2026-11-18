import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Se 5173 estiver ocupada, o Vite escolhe a próxima porta livre.
  server: { port: 5173 },
  preview: { port: 4173 },
})
