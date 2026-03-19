import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/consistency': 'http://api:8000',
            '/v2/consistency': 'http://api:8000',
        },
    },
})
