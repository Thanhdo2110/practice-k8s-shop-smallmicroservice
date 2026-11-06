import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createOrder } from '../api/orders.js'
import Alert from '../components/Alert.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { cartTotal, clearCart, removeFromCart, setQuantity, useCart } from '../lib/cart.js'
import { formatMoney } from '../lib/format.js'

export default function CartPage() {
  const cart = useCart()
  const { token, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [note, setNote] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function checkout() {
    setBusy(true)
    setError(null)
    try {
      const order = await createOrder(
        token,
        cart.map((item) => ({ productId: item.productId, quantity: item.quantity })),
        note.trim(),
      )
      clearCart()
      navigate(`/orders/${order.id}`, { state: { created: true } })
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  if (cart.length === 0) {
    return (
      <div className="card">
        <h2 className="title">Giỏ hàng</h2>
        <p className="empty">Giỏ hàng đang trống.</p>
        <Link to="/products">← Xem sản phẩm</Link>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="title">Giỏ hàng</h2>
      <Alert error={error} />
      <p className="muted" style={{ marginTop: 0 }}>
        {cart.length} món · giá lấy từ snapshot lúc thêm vào giỏ
      </p>
      <table>
        <thead>
          <tr>
            <th>Sản phẩm</th>
            <th>Giá</th>
            <th style={{ width: 140 }}>Số lượng</th>
            <th>Tạm tính</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {cart.map((item) => (
            <tr key={item.productId}>
              <td>
                <strong>{item.name}</strong>
                <div className="muted">id {item.productId}</div>
              </td>
              <td>{formatMoney(item.price)}</td>
              <td>
                <div className="row" style={{ gap: 6 }}>
                  <button className="btn btn-sm" onClick={() => setQuantity(item.productId, item.quantity - 1)}>
                    −
                  </button>
                  <input
                    style={{ width: 56, textAlign: 'center' }}
                    type="number"
                    min="1"
                    max="99"
                    value={item.quantity}
                    onChange={(event) => setQuantity(item.productId, Number(event.target.value || 1))}
                  />
                  <button className="btn btn-sm" onClick={() => setQuantity(item.productId, item.quantity + 1)}>
                    +
                  </button>
                </div>
              </td>
              <td>{formatMoney(item.price * item.quantity)}</td>
              <td>
                <button className="btn btn-danger btn-sm" onClick={() => removeFromCart(item.productId)}>
                  Bỏ
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="row spread" style={{ marginTop: 16 }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <label htmlFor="note">Ghi chú đơn (tuỳ chọn)</label>
          <input id="note" value={note} onChange={(event) => setNote(event.target.value)} maxLength={255} />
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="muted">Tổng (snapshot giỏ hàng)</div>
          <div className="price">{formatMoney(cartTotal(cart))}</div>
        </div>
      </div>

      <p className="muted">
        Lưu ý: <code>order-service</code> không tin giá ở client — nó gọi <code>product-service</code> để lấy giá và tồn
        kho thật, vì vậy tổng tiền có thể lệch nếu giá vừa thay đổi.
      </p>

      {isAuthenticated ? (
        <button className="btn btn-primary" onClick={checkout} disabled={busy}>
          {busy ? 'Đang tạo đơn…' : 'Đặt hàng'}
        </button>
      ) : (
        <div className="row">
          <Link className="btn btn-primary" to="/login" state={{ from: '/cart' }}>
            Đăng nhập để đặt hàng
          </Link>
          <button className="btn" onClick={clearCart}>
            Xoá hết giỏ
          </button>
        </div>
      )}
    </div>
  )
}
