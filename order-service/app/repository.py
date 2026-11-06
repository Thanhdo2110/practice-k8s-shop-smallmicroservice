"""Layer SQL của order-service — orders + order_items trong schema shop_orders."""
from . import db

ORDER_COLUMNS = (
    "id, user_id AS userId, username, status, total_amount AS totalAmount, note, "
    "created_at AS createdAt, updated_at AS updatedAt"
)
ITEM_COLUMNS = (
    "id, order_id AS orderId, product_id AS productId, product_name AS productName, "
    "unit_price AS unitPrice, quantity, subtotal, created_at AS createdAt"
)


def create(user, lines, total, note):
    """lines: [{productId, productName, unitPrice, quantity, subtotal}...]

    Ghi 2 bảng trong CÙNG transaction: lỗi giữa chừng -> rollback, không có
    đơn cha mà thiếu item. Snapshot tên/giá vào order_items (không JOIN catalog).
    """
    with db.transaction() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (user_id, username, status, total_amount, note) "
            "VALUES (%s, %s, 'pending', %s, %s)",
            (user["id"], user["username"], total, note),
        )
        order_id = cur.lastrowid
        for line in lines:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, subtotal) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (order_id, line["productId"], line["productName"], line["unitPrice"], line["quantity"], line["subtotal"]),
            )
        return order_id


def get_order(order_id):
    return db.fetch_one("SELECT " + ORDER_COLUMNS + " FROM orders WHERE id = %s", (order_id,))


def items_of(order_id):
    return db.fetch_all("SELECT " + ITEM_COLUMNS + " FROM order_items WHERE order_id = %s ORDER BY id", (order_id,))


def list_orders(limit, offset, user_id=None):
    where, params = "", []
    if user_id is not None:
        where = "WHERE user_id = %s"
        params.append(user_id)
    rows = db.fetch_all(
        "SELECT " + ORDER_COLUMNS + " FROM orders " + where + " ORDER BY id DESC LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    total = db.fetch_one("SELECT COUNT(*) AS total FROM orders " + where, params) or {}
    return rows, int(total.get("total", 0))


def cancel(order_id, user_id=None):
    """Chỉ đơn `pending` mới huỷ được. user_id=None => admin, không giới hạn chủ đơn.
    Trả số dòng bị update (0 = không tồn tại / sai trạng thái / không phải chủ đơn)."""
    sql = "UPDATE orders SET status = 'cancelled' WHERE id = %s AND status = 'pending'"
    params = [order_id]
    if user_id is not None:
        sql += " AND user_id = %s"
        params.append(user_id)
    return db.execute(sql, tuple(params))
