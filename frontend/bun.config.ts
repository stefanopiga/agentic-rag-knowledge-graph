// Bun configuration for ultra-fast development
import { defineConfig } from 'bun'

export default defineConfig({
  preload: ['./src/main.tsx'],
  entrypoints: ['./src/main.tsx'],
  target: 'browser',
  minify: true,
  splitting: true,
  outdir: './dist',
  root: './src',
  publicPath: '/',
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
  external: ['react', 'react-dom'],
})
