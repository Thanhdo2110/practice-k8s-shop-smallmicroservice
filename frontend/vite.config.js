import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Local dev: frontend gọi đường dẫn tương đối (/api/v1/...), Vite proxy san sang
// 3 service — mô phỏng đúng vai trò Ingress khi lên K8s.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const auth = env.AUTH_API_URL || 'http://127.0.0.1:8000'
  const catalog = env.PRODUCT_API_URL || 'http://127.0.0.1:8001'
  const orders = env.ORDER_API_URL || 'http://127.0.0.1:8002'

  const proxy = (target) => ({ target, changeOrigin: true })

  return {
    plugins: [react()],
    server: {
      host: true, // 0.0.0.0 — cần khi chạy trong pod/dev container
      port: Number(env.DEV_PORT || 5173),
      strictPort: false,
      proxy: {
        '/api/v1/auth': proxy(auth),
        '/api/v1/users': proxy(auth),
        '/api/v1/products': proxy(catalog),
        '/api/v1/categories': proxy(catalog),
        '/api/v1/orders': proxy(orders),
        '/healthz': proxy(auth),
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 700,
    },
  }
})
