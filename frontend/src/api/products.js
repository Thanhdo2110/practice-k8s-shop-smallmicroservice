import { qs, request } from './http.js'

export async function fetchProducts(params = {}) {
  return request(`/api/v1/products/${qs({ page: 1, pageSize: 12, sort: '-created', ...params })}`)
}

export async function fetchProduct(id, token) {
  const { data } = await request(`/api/v1/products/${id}`, { token })
  return data
}

export async function fetchCategories() {
  const { data } = await request('/api/v1/categories')
  return data
}

export async function createProduct(token, payload) {
  const { data } = await request('/api/v1/products/', { method: 'POST', body: payload, token })
  return data
}

export async function updateProduct(token, id, payload) {
  const { data } = await request(`/api/v1/products/${id}`, { method: 'PUT', body: payload, token })
  return data
}

export async function deleteProduct(token, id) {
  const { data } = await request(`/api/v1/products/${id}`, { method: 'DELETE', token })
  return data
}
