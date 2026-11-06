import { qs, request } from './http.js'

export async function login(username, password) {
  const { data } = await request('/api/v1/auth/login', { method: 'POST', body: { username, password } })
  return data
}

export async function register(payload) {
  const { data } = await request('/api/v1/auth/register', { method: 'POST', body: payload })
  return data
}

export async function fetchMe(token) {
  const { data } = await request('/api/v1/auth/me', { token })
  return data
}

export async function fetchUsers(token, page = 1, pageSize = 20) {
  return request(`/api/v1/users/${qs({ page, pageSize })}`, { token })
}
