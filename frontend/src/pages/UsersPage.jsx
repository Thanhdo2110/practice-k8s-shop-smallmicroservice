import { useCallback, useEffect, useState } from 'react'
import { fetchUsers } from '../api/auth.js'
import Alert from '../components/Alert.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { formatDateTime } from '../lib/format.js'

export default function UsersPage() {
  const { token } = useAuth()
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState({ page: 1, pageSize: 20, total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchUsers(token, meta.page, meta.pageSize)
      setRows(response.data || [])
      setMeta(response.meta || meta)
    } catch (caught) {
      setRows([])
      setError(caught)
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta.page, meta.pageSize, token])

  useEffect(() => {
    load()
  }, [load])

  const pageCount = Math.max(1, Math.ceil(meta.total / meta.pageSize))

  return (
    <div className="card">
      <div className="row spread">
        <h2 className="title">Người dùng</h2>
        <button className="btn btn-sm" onClick={load} disabled={loading}>
          Làm mới
        </button>
      </div>
      <p className="muted">
        Endpoint <code>GET /api/v1/users/</code> chỉ mở cho role <code>admin</code> (decorator <code>require_role</code>).
      </p>
      <Alert error={error} />
      {loading && <p className="muted">Đang tải từ auth-service…</p>}

      {!loading && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Email</th>
              <th>Họ tên</th>
              <th>Role</th>
              <th>Tạo lúc</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.username}</td>
                <td>{row.email}</td>
                <td>{row.fullName || '—'}</td>
                <td>
                  <span className={`pill pill-${row.role}`}>{row.role}</span>
                </td>
                <td>{formatDateTime(row.createdAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && rows.length === 0 && !error && <p className="empty">Chưa có user nào trong shop_auth.</p>}

      <div className="row" style={{ marginTop: 16 }}>
        <button className="btn btn-sm" disabled={meta.page <= 1} onClick={() => setMeta({ ...meta, page: meta.page - 1 })}>
          ← Trước
        </button>
        <span className="muted">
          {meta.page} / {pageCount} · {meta.total} user
        </span>
        <button className="btn btn-sm" disabled={meta.page >= pageCount} onClick={() => setMeta({ ...meta, page: meta.page + 1 })}>
          Sau →
        </button>
      </div>
    </div>
  )
}
