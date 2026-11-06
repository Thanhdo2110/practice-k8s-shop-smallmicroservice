// Cấu hình runtime của frontend.
// VITE_API_BASE_URL rỗng => gọi same-origin, dựa vào Vite proxy (dev) hoặc Ingress (K8s).
// Lưu ý: biến VITE_* được nhúng HARD-CODE vào bundle lúc `vite build`,
// nên `kubectl set env` trên Deployment frontend sẽ KHÔNG đổi được gì.
const raw = import.meta.env.VITE_API_BASE_URL ?? ''

export const API_BASE = raw.replace(/\/+$/, '')
export const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'Shop K8s'
export const TOKEN_KEY = 'shop.accessToken'
export const USER_KEY = 'shop.user'
