import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  build: {
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if(assetInfo.name?.endsWith('.whl')) {
            return "[name].[ext]";
          }
          return "[name]-[hash].[ext]"

        }
      }
    },
    assetsInlineLimit: (file) => {
      return !file.endsWith('.whl');
      
  }
  }
})
