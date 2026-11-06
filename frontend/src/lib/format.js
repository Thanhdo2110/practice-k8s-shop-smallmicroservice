export function formatMoney(value) {
  const number = Number(value || 0)
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(number)
}

export function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

export function statusLabel(status) {
  return { pending: 'Chờ xử lý', paid: 'Đã thanh toán', done: 'Hoàn tất', cancelled: 'Đã huỷ' }[status] || status
}
