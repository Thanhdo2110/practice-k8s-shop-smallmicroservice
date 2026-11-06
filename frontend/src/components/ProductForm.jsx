import { useState } from 'react'
import Alert from './Alert.jsx'

const EMPTY = { name: '', description: '', price: '', stock: 0, category: 'other', imageUrl: '' }

export default function ProductForm({ initial, categories = [], onSubmit, onClose }) {
  const [values, setValues] = useState(() => ({ ...EMPTY, ...initial }))
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const bind = (key) => (event) => setValues((current) => ({ ...current, [key]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    if (!values.name.trim()) {
      setError({ message: 'Tên sản phẩm là bắt buộc', code: 'FIELD_REQUIRED' })
      return
    }
    setSaving(true)
    setError(null)
    try {
      await onSubmit({
        name: values.name.trim(),
        description: values.description.trim(),
        price: Number(values.price || 0),
        stock: Number(values.stock || 0),
        category: values.category.trim() || 'other',
        imageUrl: values.imageUrl.trim(),
      })
      onClose()
    } catch (caught) {
      setError(caught)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal" onClick={onClose}>
      <form className="card modal-card" onClick={(event) => event.stopPropagation()} onSubmit={handleSubmit}>
        <h3 className="title">{initial?.id ? `Sửa sản phẩm #${initial.id}` : 'Thêm sản phẩm'}</h3>
        <Alert error={error} />

        <label htmlFor="name">Tên sản phẩm</label>
        <input id="name" value={values.name} onChange={bind('name')} maxLength={160} />

        <div className="row">
          <div className="field-wide">
            <label htmlFor="price">Giá (VND)</label>
            <input id="price" type="number" min="0" step="1000" value={values.price} onChange={bind('price')} />
          </div>
          <div className="field-wide">
            <label htmlFor="stock">Tồn kho</label>
            <input id="stock" type="number" min="0" step="1" value={values.stock} onChange={bind('stock')} />
          </div>
        </div>

        <label htmlFor="category">Nhóm hàng</label>
        <input id="category" list="category-options" value={values.category} onChange={bind('category')} maxLength={64} />
        <datalist id="category-options">
          {categories.map((item) => (
            <option key={item.category} value={item.category} />
          ))}
        </datalist>

        <label htmlFor="imageUrl">Ảnh (URL)</label>
        <input id="imageUrl" value={values.imageUrl} onChange={bind('imageUrl')} maxLength={512} />

        <label htmlFor="description">Mô tả</label>
        <textarea id="description" rows={3} value={values.description} onChange={bind('description')} maxLength={2000} />

        <div className="row spread" style={{ marginTop: 18 }}>
          <button type="button" className="btn" onClick={onClose}>
            Huỷ
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Đang lưu…' : 'Lưu sản phẩm'}
          </button>
        </div>
      </form>
    </div>
  )
}
