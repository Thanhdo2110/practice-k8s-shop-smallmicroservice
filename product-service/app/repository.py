"""Layer SQL của product-service — bảng products trong schema shop_catalog."""
from . import db
from .errors import bad_request

COLUMNS = (
    "id, name, description, price, stock, category, "
    "image_url AS imageUrl, created_at AS createdAt, updated_at AS updatedAt"
)
SORTABLE = {"created": "created_at", "price": "price", "name": "name", "stock": "stock"}
UPDATABLE = {
    "name": "name",
    "description": "description",
    "price": "price",
    "stock": "stock",
    "category": "category",
    "imageUrl": "image_url",
}


def _filters(q, category):
    where = ["deleted_at IS NULL"]
    params = []
    if q:
        where.append("(name LIKE %s OR description LIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    if category:
        where.append("category = %s")
        params.append(category)
    return " AND ".join(where), params


def _order_by(sort):
    column = (sort or "created").lstrip("-")
    if column not in SORTABLE:
        raise bad_request(
            f"sort không hợp lệ, cho phép: {', '.join(SORTABLE)} (thêm '-' để giảm dần)",
            code="SORT_INVALID",
        )
    direction = "DESC" if (sort or "").startswith("-") else "ASC"
    return f"{SORTABLE[column]} {direction}, id ASC"  # khoá phụ phụ -> phân trang ổn định


def search(q, category, sort, limit, offset):
    clause, params = _filters(q, category)
    rows = db.fetch_all(
        "SELECT " + COLUMNS + " FROM products WHERE " + clause
        + " ORDER BY " + _order_by(sort) + " LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    total = db.fetch_one("SELECT COUNT(*) AS total FROM products WHERE " + clause, params)
    return rows, int((total or {}).get("total", 0))


def get_by_id(product_id):
    return db.fetch_one("SELECT " + COLUMNS + " FROM products WHERE id = %s AND deleted_at IS NULL", (product_id,))


def create(name, description, price, stock, category, image_url):
    return db.insert_returning_id(
        "INSERT INTO products (name, description, price, stock, category, image_url) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (name, description, price, stock, category, image_url),
    )


def update(product_id, values):
    items = [(UPDATABLE[key], values[key]) for key in UPDATABLE if key in values]
    if not items:
        return 0
    sets = ", ".join(f"{column} = %s" for column, _ in items)
    params = [value for _, value in items]
    return db.execute(
        "UPDATE products SET " + sets + " WHERE id = %s AND deleted_at IS NULL",
        params + [product_id],
    )


def soft_delete(product_id):
    return db.execute("UPDATE products SET deleted_at = NOW() WHERE id = %s AND deleted_at IS NULL", (product_id,))


def categories():
    return db.fetch_all(
        "SELECT category, COUNT(*) AS productCount FROM products "
        "WHERE deleted_at IS NULL GROUP BY category ORDER BY productCount DESC, category ASC"
    )
