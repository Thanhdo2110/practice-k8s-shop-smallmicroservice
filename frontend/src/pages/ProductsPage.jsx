import { useCallback, useEffect, useState } from 'react'
import {
  createProduct,
  deleteProduct,
  fetchCategories,
  fetchProducts,
  updateProduct,
} from '../api/products.js'
import Alert from '../components/Alert.jsx'
import ProductForm from '../components/ProductForm.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { addToCart } from '../lib/cart.js'
import { formatMoney } from '../lib/format.js'

const SORTS = [
  { value: '-created', label: 'Mới nhất' },
  { value: 'price', label: 'Giá thấp → cao' },
  { value: '-price', label: 'Giá cao → thấp' },
  { value: 'name', label: 'Tên A → Z' },
]

export default function ProductsPage() {
  const { token, isAdmin } = useAuth()
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState({ page: 1, pageSize: 12, total: 0 })
  const [categories, setCategories] = useState([])
  const [filters, setFilters] = useState({ q: '', category: '', sort: '-created', page: 1 })
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(null)
  const [toast, setToast] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchProducts({ ...filters, pageSize: meta.pageSize })
      setItems(response.data || [])
      setMeta(response.meta || { page: 1, pageSize: 12, total: 0 })
    } catch (caught) {
      setItems([])
      setError(caught)
    } finally {
      setLoading(false)
    }
  }, [filters, meta.pageSize])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    if (!toast) return undefined
    const timer = setTimeout(() => setToast(''), 2500)
    return () => clearTimeout(timer)
  }, [toast])

  const patch = (next) => setFilters((current) => ({ ...current, page: 1, ...next }))

  async function handleCreateOrUpdate(payload) {
    if (editing?.id) {
      await updateProduct(token, editing.id, payload)
      setToast(`Đã cập nhật "${payload.name}"`)
    } else {
      await createProduct(token, payload)
      setToast(`Đã thêm sản phẩm "${payload.name}"`)
    }
    load()
  }

  async function handleDelete(product) {
    if (!window.confirm(`Xoá "${product.name}" khỏi catalog?`)) return
    try {
      await deleteProduct(token, product.id)
      setToast(`Đã xoá "${product.name}"`)
      setError(null)
      load()
    } catch (caught) {
      setError(caught)
    }
  }

  const pageCount = Math.max(1, Math.ceil(meta.total / meta.pageSize))

  return (
    <>
      <div className="card">
        <div className="row spread">
          <div>
            <h2 className="title">Catalog</h2>
            <p className="muted" style={{ margin: 0 }}>
              {loading ? 'Đang tải từ product-service…' : `${meta.total} sản phẩm · trang ${meta.page}/${pageCount}`}
            </p>
          </div>
          <div className="row">
            {isAdmin && (
              <button className="btn btn-primary" onClick={() => setEditing({})}>
                + Thêm sản phẩm
              </button>
            )}
          </div>
        </div>

        <form
          className="row"
          style={{ marginTop: 14 }}
          onSubmit={(event) => {
            event.preventDefault()
            patch({ q: keyword.trim() })
          }}
        >
          <div className="field-wide">
            <input placeholder="Tìm theo tên hoặc mô tả…" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
          </div>
          <div className="field-wide">
            <select value={filters.category} onChange={(event) => patch({ category: event.target.value })}>
              <option value="">Tất cả nhóm hàng</option>
              {categories.map((item) => (
                <option key={item.category} value={item.category}>
                  {item.category} ({item.productCount})
                </option>
              ))}
            </select>
          </div>
          <div className="field-wide">
            <select value={filters.sort} onChange={(event) => patch({ sort: event.target.value })}>
              {SORTS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <button className="btn" type="submit">
            Lọc
          </button>
        </form>

        <Alert error={error} />
        {!loading && !error && items.length === 0 && <p className="empty">Không có sản phẩm nào khớp bộ lọc.</p>}
      </div>

      {toast && <Alert kind="info">{toast}</Alert>}

      <div className="grid">
        {items.map((product) => (
          <article className="card product" key={product.id}>
            {product.imageUrl ? (
              <img src={product.imageUrl} alt={product.name} loading="lazy" />
            ) : (
              <div style={{ height: 170, background: '#f1f5f9' }} />
            )}
            <div className="product-body">
              <div className="row spread">
                <span className="pill">{product.category}</span>
                <span className="muted">#{product.id}</span>
              </div>
              <h3 className="product-name">{product.name}</h3>
              <p className="product-desc">{product.description || 'Chưa có mô tả'}</p>
              <div className="row spread">
                <span className="price">{formatMoney(product.price)}</span>
                {Number(product.stock) > 0 ? (
                  <span className="muted">còn {product.stock}</span>
                ) : (
                  <span className="out-of-stock">hết hàng</span>
                )}
              </div>
              <div className="row">
                <button
                  className="btn btn-primary btn-sm"
                  disabled={Number(product.stock) <= 0}
                  onClick={() => {
                    addToCart(product, 1)
                    setToast(`Đã thêm "${product.name}" vào giỏ`)
                  }}
                >
                  Thêm vào giỏ
                </button>
                {isAdmin && (
                  <>
                    <button className="btn btn-sm" onClick={() => setEditing(product)}>
                      Sửa
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(product)}>
                      Xoá
                    </button>
                  </>
                )}
              </div>
            </div>
          </article>
        ))}
        {loading &&
          Array.from({ length: 4 }).map((_, index) => (
            <div className="skeleton" key={index}>
              <span className="empty">product-service…</span>
            </div>
          ))}
      </div>

      <div className="row" style={{ marginTop: 18, justifyContent: 'center' }}>
        <button className="btn" disabled={meta.page <= 1 || loading} onClick={() => setFilters({ ...filters, page: meta.page - 1 })}>
          ← Trang trước
        </button>
        <span className="muted">
          {meta.page} / {pageCount}
        </span>
        <button
          className="btn"
          disabled={meta.page >= pageCount || loading}
          onClick={() => setFilters({ ...filters, page: meta.page + 1 })}
        >
          Trang sau →
        </button>
      </div>

      {editing && (
        <ProductForm
          initial={editing.id ? editing : undefined}
          categories={categories}
          onSubmit={handleCreateOrUpdate}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  )
}
