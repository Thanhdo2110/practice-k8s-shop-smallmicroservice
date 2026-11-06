import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { cancelOrder, fetchOrder } from '../api/orders.js'
import Alert from '../components/Alert.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { formatDateTime, formatMoney, statusLabel } from '../lib/format.js'

export default function OrderDetailPage() {
  const { id } = useParams()
  const { token, user } = useAuth()
  const location = useLocation()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError(null)
    fetchOrder(token, id)
      .then(setOrder)
      .catch((caught) => {
        setOrder(null)
        setError(caught)
      })
  }, [token, id])

  useEffect(() => {
    load()
  }, [load])

  async function handleCancel() {
    setBusy(true)
    setError(null)
    try {
      setOrder(await cancelOrder(token, id))
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  const isOwner = order && String(order.userId) === String(user?.id)
  const canCancel = order && order.status === 'pending' && (user?.role === 'admin' || isOwner)

  return (
    <div className="card">
      {location.state?.created && <Alert kind="info">Đã tạo đơn hàng. order-service lấy giá từ product-service lúc đặt.</Alert>}
      <div className="row spread">
        <h2 className="title">Đơn #{id}</h2>
        <Link to="/orders">← Danh sách đơn</Link>
      </div>

      <Alert error={error} />
      {error?.code === 'ORDER_FORBIDDEN' && (
        <p className="muted">Đơn này không thuộc tài khoản của bạn (order-service check `user_id` từ JWT).</p>
      )}

      {order && (
        <>
          <div className="row" style={{ gap: 24 }}>
            <div>
              <div className="muted">Khách hàng</div>
              <strong>{order.username}</strong> (id {order.userId})
            </div>
            <div>
              <div className="muted">Trạng thái</div>
              <strong className={`status-${order.status}`}>{statusLabel(order.status)}</strong>
            </div>
            <div>
              <div className="muted">Tạo lúc</div>
              <strong>{formatDateTime(order.createdAt)}</strong>
            </div>
            {order.note && (
              <div>
                <div className="muted">Ghi chú</div>
                <strong>{order.note}</strong>
              </div>
            )}
          </div>

          <table style={{ marginTop: 16 }}>
            <thead>
              <tr>
                <th>Sản phẩm</th>
                <th>Giá đơn vị</th>
                <th>SL</th>
                <th>Tạm tính</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    {item.productName} <span className="muted">(id {item.productId})</span>
                  </td>
                  <td>{formatMoney(item.unitPrice)}</td>
                  <td>{item.quantity}</td>
                  <td>{formatMoney(item.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="row spread" style={{ marginTop: 16 }}>
            <div className="price">Tổng: {formatMoney(order.totalAmount)}</div>
            {canCancel && (
              <button className="btn btn-danger" onClick={handleCancel} disabled={busy}>
                {busy ? 'Đang huỷ…' : 'Huỷ đơn'}
              </button>
            )}
          </div>
          <p className="muted">
            Snapshot `product_name`/`unit_price` lưu trong shop_orders — sang catalog xem sản phẩm đã đổi giá/chưa.
          </p>
        </>
      )}
    </div>
  )
}
