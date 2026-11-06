import { useSyncExternalStore } from 'react'

const KEY = 'shop.cart'
const listeners = new Set()
let cache = { raw: null, items: [] }

function parse(raw) {
  try {
    const items = JSON.parse(raw || '[]')
    return Array.isArray(items) ? items.filter((item) => item && item.productId > 0 && item.quantity > 0) : []
  } catch {
    return []
  }
}

function emit() {
  listeners.forEach((listener) => listener())
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

// useSyncExternalStore cần trả về đúng một tham chiếu khi dữ liệu không đổi
function getSnapshot() {
  const raw = typeof localStorage === 'undefined' ? '[]' : localStorage.getItem(KEY) || '[]'
  if (raw !== cache.raw) cache = { raw, items: parse(raw) }
  return cache.items
}

function write(items) {
  localStorage.setItem(KEY, JSON.stringify(items))
  emit()
}

export function useCart() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
}

export function cartCount(items) {
  return items.reduce((sum, item) => sum + item.quantity, 0)
}

export function cartTotal(items) {
  return Math.round(items.reduce((sum, item) => sum + item.price * item.quantity, 0))
}

export function addToCart(product, quantity = 1) {
  const items = getSnapshot().slice()
  const found = items.find((item) => item.productId === product.id)
  if (found) {
    found.quantity = Math.min(99, found.quantity + quantity)
  } else {
    items.push({
      productId: product.id,
      name: product.name,
      price: Number(product.price) || 0,
      stock: Number(product.stock) || 0,
      image: product.imageUrl || '',
      quantity,
    })
  }
  write(items)
}

export function setQuantity(productId, quantity) {
  const items = getSnapshot()
    .map((item) => (item.productId === productId ? { ...item, quantity: Math.max(0, Math.min(99, quantity)) } : item))
    .filter((item) => item.quantity > 0)
  write(items)
}

export function removeFromCart(productId) {
  write(getSnapshot().filter((item) => item.productId !== productId))
}

export function clearCart() {
  write([])
}
