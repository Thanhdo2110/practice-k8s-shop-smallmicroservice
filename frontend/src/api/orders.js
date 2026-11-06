import { qs, request } from './http.js'

export async function createOrder(token, items, note = '') {
  const { data } = await request('/api/v1/orders/', { method: 'POST', body: { items, note }, token })
  return data
}

export async function fetchOrders(token, params = {}) {
  return request(`/api/v1/orders/${qs({ page: 1, pageSize: 10, ...params })}`, { token })
}

export async function fetchOrder(token, id) {
  const { data } = await request(`/api/v1/orders/${id}`, { token })
  return data
}

export async function cancelOrder(token, id) {
  const { data } = await request(`/api/v1/orders/${id}/cancel`, { method: 'POST', token })
  return data
}
