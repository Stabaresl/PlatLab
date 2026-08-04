import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { ViteImageOptimizer } from 'vite-plugin-image-optimizer'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // RNF rendimiento — grim.png (fondo del hero) pesaba 3.77MB sin
    // comprimir; term.png y logo-platlab.png también se servían tal
    // cual se subieron. Comprime en el build, no hace falta tocar los
    // imports ni convertir de formato a mano.
    ViteImageOptimizer({
      // Solo raster (png/jpg) — los .svg del proyecto son íconos hechos a
      // mano, no capturas pesadas; optimizarlos necesitaría `svgo` aparte
      // y no es el problema que esto resuelve.
      test: /\.(png|jpe?g)$/i,
      png: { quality: 75 },
      jpeg: { quality: 75 },
      jpg: { quality: 75 },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
