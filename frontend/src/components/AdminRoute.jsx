import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin, booting } = useAuth()

  if (booting) return <p className="muted">Đang kiểm tra phiên…</p>
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!isAdmin) return <Navigate to="/products" replace />
  return children
}
