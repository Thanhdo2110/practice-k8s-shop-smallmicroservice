import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { cartCount, useCart } from '../lib/cart.js'
import { APP_TITLE } from '../lib/config.js'

export default function Layout() {
  const { user, isAuthenticated, isAdmin, logout, booting } = useAuth()
  const cart = useCart()
  const navigate = useNavigate()
  const count = cartCount(cart)

  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <NavLink to="/products" className="brand">
            {APP_TITLE} <span>v1</span>
          </NavLink>
          <nav className="nav">
            <NavLink to="/products">Sản phẩm</NavLink>
            <NavLink to="/cart">
              Giỏ hàng{count > 0 && <em className="badge-count">{count}</em>}
            </NavLink>
            {isAuthenticated && <NavLink to="/orders">Đơn của tôi</NavLink>}
            {isAdmin && <NavLink to="/admin/users">Users</NavLink>}
          </nav>
          <div className="user-box">
            {isAuthenticated ? (
              <>
                <span>
                  {user?.fullName || user?.username} <em className={`pill pill-${user?.role}`}>{user?.role}</em>
                </span>
                <button
                  className="btn btn-sm"
                  onClick={() => {
                    logout()
                    navigate('/login')
                  }}
                >
                  Đăng xuất
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login">Đăng nhập</NavLink>
                <NavLink to="/register">Tạo tài khoản</NavLink>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="main">{booting ? <p className="muted">Đang kiểm tra phiên…</p> : <Outlet />}</main>
      <footer className="app-footer">
        Demo microservices trên Kubernetes: auth-service · product-service · order-service · MySQL
      </footer>
    </>
  )
}
