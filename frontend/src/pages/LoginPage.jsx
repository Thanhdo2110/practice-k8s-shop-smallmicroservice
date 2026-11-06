import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import Alert from '../components/Alert.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const from = location.state?.from || '/products'

  if (isAuthenticated) return <Navigate to={from} replace />

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(form.username.trim(), form.password)
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card auth-card">
      <h2 className="title">Đăng nhập</h2>
      <p className="muted">Tài khoản đầu tiên bạn đăng ký sẽ tự nhận role admin.</p>
      <Alert error={error} />
      <form onSubmit={handleSubmit}>
        <label htmlFor="username">Tên đăng nhập hoặc email</label>
        <input
          id="username"
          value={form.username}
          onChange={(event) => setForm({ ...form, username: event.target.value })}
          autoComplete="username"
        />
        <label htmlFor="password">Mật khẩu</label>
        <input
          id="password"
          type="password"
          value={form.password}
          onChange={(event) => setForm({ ...form, password: event.target.value })}
          autoComplete="current-password"
        />
        <div className="row spread" style={{ marginTop: 18 }}>
          <button type="submit" className="btn btn-primary" disabled={busy || !form.username || !form.password}>
            {busy ? 'Đang vào…' : 'Đăng nhập'}
          </button>
          <Link to="/register">Chưa có tài khoản?</Link>
        </div>
      </form>
    </div>
  )
}
