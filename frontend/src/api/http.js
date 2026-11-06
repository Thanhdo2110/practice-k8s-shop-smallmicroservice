import { API_BASE } from '../lib/config.js'

function requestId() {
  return globalThis.crypto?.randomUUID?.().slice(0, 12) || Math.random().toString(16).slice(2, 14)
}

export function qs(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

/** Gọi API, luôn trả JSON envelope {data, meta}. Lỗi ném Error có .code/.status. */
export async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { Accept: 'application/json', 'X-Request-Id': requestId() }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (cause) {
    const error = new Error('Không kết nối được API. Kiểm tra Ingress/Service hoặc `kubectl logs`.')
    error.code = 'NETWORK_ERROR'
    error.cause = cause
    throw error
  }

  const text = await response.text()
  let payload = null
  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    payload = null
  }

  if (!response.ok) {
    const error = new Error(payload?.error?.message || `HTTP ${response.status}`)
    error.code = payload?.error?.code || 'HTTP_ERROR'
    error.status = response.status
    error.details = payload?.error?.details
    error.requestId = headers['X-Request-Id']
    throw error
  }
  return payload || { data: null }
}
