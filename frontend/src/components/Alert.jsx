export default function Alert({ kind = 'error', error, children }) {
  let message = children
  if (error) {
    const parts = [error.message || String(error)]
    if (error.code) parts.push(`[${error.code}]`)
    if (error.requestId) parts.push(`(requestId: ${error.requestId})`)
    message = parts.join(' ')
  }
  if (!message) return null
  return (
    <div className={`banner banner-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {message}
    </div>
  )
}
