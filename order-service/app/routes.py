"""HTTP layer order-service: tạo đơn hàng, lịch sử đơn, huỷ đơn.

Giá/tên sản phẩm KHÔNG lấy từ body của client — luôn hỏi product-service,
đây là lý do order-service tồn tại như một service độc lập.
"""
from flask import Blueprint, g, jsonify, request

from . import catalog_client
from . import repository as repo
from .config import Config
from .errors import bad_request, conflict, forbidden, not_found
from .security import require_auth

orders_bp = Blueprint("orders", __name__)

MAX_QUANTITY_PER_ITEM = 99


def _body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise bad_request("Body phải là JSON object", code="INVALID_JSON")
    return data


def _int_arg(name, default, minimum, maximum):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise bad_request(f"Query '{name}' phải là số", code="QUERY_INVALID")
    return min(maximum, max(minimum, value))


def _normalise_items(raw_items):
    """[{productId, quantity}] -> {product_id: quantity}, cộng gộp trùng lặp."""
    if not isinstance(raw_items, list) or not raw_items:
        raise bad_request("Field 'items' phải là mảng không rỗng", code="ITEMS_REQUIRED")
    if len(raw_items) > Config.MAX_ITEMS_PER_ORDER:
        raise bad_request(f"Tối đa {Config.MAX_ITEMS_PER_ORDER} dòng sản phẩm/đơn", code="TOO_MANY_ITEMS")

    merged = {}
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise bad_request(f"items[{index}] phải là object", code="ITEM_INVALID")
        try:
            product_id = int(item.get("productId"))
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError):
            raise bad_request(f"items[{index}] cần productId/quantity là số", code="ITEM_INVALID")
        if product_id <= 0:
            raise bad_request(f"items[{index}].productId không hợp lệ", code="ITEM_INVALID")
        if quantity < 1 or quantity > MAX_QUANTITY_PER_ITEM:
            raise bad_request(f"items[{index}].quantity phải trong [1, {MAX_QUANTITY_PER_ITEM}]", code="QUANTITY_RANGE")
        merged[product_id] = merged.get(product_id, 0) + quantity
    for product_id, quantity in merged.items():
        if quantity > MAX_QUANTITY_PER_ITEM:
            raise bad_request(
                f"Sản phẩm {product_id} vượt {MAX_QUANTITY_PER_ITEM} cái sau khi gộp trùng",
                code="QUANTITY_RANGE",
            )
    return merged


def _payload(order_id):
    order = repo.get_order(order_id)
    if not order:
        raise not_found("Không tìm thấy đơn hàng", code="ORDER_NOT_FOUND")
    order["items"] = repo.items_of(order_id)
    return order


def _can_access(order):
    return g.user["role"] == "admin" or int(order["userId"]) == int(g.user["id"])


# --------------------------------------------------------------------------- create
@orders_bp.post("")
@orders_bp.post("/")
@require_auth
def create_order():
    data = _body()
    note = data.get("note") if isinstance(data.get("note"), str) else ""
    note = note.strip()[:255]
    requested = _normalise_items(data.get("items"))

    lines = []
    total = 0.0
    for product_id, quantity in requested.items():
        product = catalog_client.fetch_product(product_id, g.get("request_id", ""))
        if not product:
            raise bad_request(f"Sản phẩm {product_id} không tồn tại", code="PRODUCT_NOT_FOUND")
        stock = int(product.get("stock") or 0)
        if stock < quantity:
            raise bad_request(
                f"'{product.get('name')}' chỉ còn {stock}, bạn muốn {quantity}",
                code="STOCK_NOT_ENOUGH",
                details={"productId": product_id, "stock": stock, "requested": quantity},
            )
        unit_price = round(float(product.get("price") or 0), 2)
        subtotal = round(unit_price * quantity, 2)
        total += subtotal
        lines.append(
            {
                "productId": product_id,
                "productName": str(product.get("name", ""))[:160],
                "unitPrice": unit_price,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    order_id = repo.create(g.user, lines, round(total, 2), note)
    return jsonify({"data": _payload(order_id), "meta": {"pricedBy": Config.PRODUCT_SERVICE_BASE_URL}}), 201


# ---------------------------------------------------------------------------- read
@orders_bp.get("")
@orders_bp.get("/")
@require_auth
def list_orders():
    page = _int_arg("page", 1, 1, 10_000)
    size = _int_arg("pageSize", 10, 1, 50)
    want_all = (request.args.get("scope") or "").lower() == "all"
    if want_all and g.user["role"] != "admin":
        raise forbidden("Chỉ admin mới xem được toàn bộ đơn", code="ROLE_DENIED")
    user_id = None if want_all else g.user["id"]

    items, total = repo.list_orders(size, (page - 1) * size, user_id)
    return jsonify(
        {
            "data": items,
            "meta": {"page": page, "pageSize": size, "total": total, "scope": "all" if want_all else "mine"},
        }
    )


@orders_bp.get("/<int:order_id>")
@require_auth
def get_order(order_id):
    order = _payload(order_id)
    if not _can_access(order):
        raise forbidden("Đơn hàng không thuộc về bạn", code="ORDER_FORBIDDEN")
    return jsonify({"data": order})


# -------------------------------------------------------------------------- cancel
@orders_bp.post("/<int:order_id>/cancel")
@require_auth
def cancel_order(order_id):
    order = repo.get_order(order_id)
    if not order:
        raise not_found("Không tìm thấy đơn hàng", code="ORDER_NOT_FOUND")
    if not _can_access(order):
        raise forbidden("Đơn hàng không thuộc về bạn", code="ORDER_FORBIDDEN")

    affected = repo.cancel(order_id, None if g.user["role"] == "admin" else g.user["id"])
    if not affected:
        raise conflict(f"Không huỷ được: đơn đang ở trạng thái '{order['status']}'", code="CANCEL_NOT_ALLOWED")
    return jsonify({"data": _payload(order_id)})
