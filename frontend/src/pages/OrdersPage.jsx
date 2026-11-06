import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchOrders } from '../api/orders.js'
import Alert from '../components/Alert.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { formatDateTime, formatMoney, statusLabel } from '../lib/format.js'

export default function OrdersPage() {
  const { token, isAdmin } = useAuth()
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState({ page: 1, pageSize: 10, total: 0 })
  const [scope, setScope] = useState('mine')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchOrders(token, {
        page: meta.page,
        pageSize: meta.pageSize,
        scope: isAdmin && scope === 'all' ? 'all' : undefined,
      })
      setRows(response.data || [])
      setMeta(response.meta || meta)
    } catch (caught) {
      setRows([])
      setError(caught)
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta.page, meta.pageSize, scope, isAdmin, token])

  useEffect(() => {
    load()
  }, [load])

  const pageCount = Math.max(1, Math.ceil(meta.total / meta.pageSize))

  return (
    <div className="card">
      <div className="row spread">
        <h2 className="title">Đơn hàng</h2>
        <div className="row">
          {isAdmin && (
            <select
              value={scope}
              style={{ width: 190 }}
              onChange={(event) => {
                setScope(event.target.value)
                setMeta({ ...meta, page: 1 })
              }}
            >
              <option value="mine">Đơn của tôi</option>
              <option value="all">Tất cả (admin)</option>
            </select>
          )}
          <button className="btn btn-sm" onClick={load} disabled={loading}>
            Làm mới
          </button>
        </div>
      </div>

      <Alert error={error} />
      {loading && <p className="muted">Đang tải từ order-service…</p>}
      {!loading && rows.length === 0 && !error && (
        <p className="empty">
          Chưa có đơn nào. <Link to="/products">Đi mua hàng</Link>
        </p>
      )}

      {!loading && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>#</th>
              {scope === 'all' && <th>Khách</th>}
              <th>Trạng thái</th>
              <th>Tổng tiền</th>
              <th>Tạo lúc</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((order) => (
              <tr key={order.id}>
                <td>{order.id}</td>
                {scope === 'all' && <td>{order.username}</td>}
                <td className={`status-${order.status}`}>{statusLabel(order.status)}</td>
                <td>{formatMoney(order.totalAmount)}</td>
                <td>{formatDateTime(order.createdAt)}</td>
                <td>
                  <Link to={`/orders/${order.id}`}>Chi tiết</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="row" style={{ marginTop: 16 }}>
        <button
          className="btn btn-sm"
          disabled={meta.page <= 1}
          onClick={() => setMeta({ ...meta, page: meta.page - 1 })}
        >
          ← Trước
        </button>
        <span className="muted">
          {meta.page} / {pageCount} · {meta.total} đơn
        </span>
        <button
          className="btn btn-sm"
          disabled={meta.page >= pageCount}
          onClick={() => setMeta({ ...meta, page: meta.page + 1 })}
        >
          Sau →
        </button>
      </div>
    </div>
  )
}
