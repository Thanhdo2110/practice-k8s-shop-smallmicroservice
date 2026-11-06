import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import Alert from '../components/Alert.jsx'
import { useAuth } from '../context/AuthContext.jsx'

const EMPTY = { username: '', email: '', fullName: '', password: '', confirm: '' }

export default function RegisterPage() {
  const { register, login, isAuthenticated, isAdmin } = useAuth()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (isAuthenticated) return <Navigate to="/products" replace />

  const bind = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    if (form.password !== form.confirm) {
      setError({ message: 'Mật khẩu nhập lại không khớp', code: 'PASSWORD_MISMATCH' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      await register({
        username: form.username.trim(),
        email: form.email.trim(),
        fullName: form.fullName.trim(),
        password: form.password,
      })
      // đăng ký xong đăng nhập luôn cho tiện
      await login(form.username.trim(), form.password)
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card auth-card">
      <h2 className="title">Tạo tài khoản</h2>
      {isAuthenticated && !isAdmin && <Alert kind="info">Bạn đã đăng nhập.</Alert>}
      <Alert error={error} />
      <form onSubmit={handleSubmit}>
        <label htmlFor="username">Tên đăng nhập (3-32 ký tự, a-z 0-9 . _)</label>
        <input id="username" value={form.username} onChange={bind('username')} maxLength={32} />

        <label htmlFor="email">Email</label>
        <input id="email" type="email" value={form.email} onChange={bind('email')} maxLength={255} />

        <label htmlFor="fullName">Họ tên (tuỳ chọn)</label>
        <input id="fullName" value={form.fullName} onChange={bind('fullName')} maxLength={128} />

        <label htmlFor="password">Mật khẩu (tối thiểu 8 ký tự)</label>
        <input id="password" type="password" value={form.password} onChange={bind('password')} autoComplete="new-password" />

        <label htmlFor="confirm">Nhập lại mật khẩu</label>
        <input id="confirm" type="password" value={form.confirm} onChange={bind('confirm')} autoComplete="new-password" />

        <div className="row spread" style={{ marginTop: 18 }}>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang tạo…' : 'Đăng ký'}
          </button>
          <Link to="/login">Đã có tài khoản?</Link>
        </div>
      </form>
    </div>
  )
}
