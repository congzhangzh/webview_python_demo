import { defineConfig } from './$node_modules/vite/dist/node/index.js'
import react from './$node_modules/@vitejs/plugin-react/dist/index.mjs'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
