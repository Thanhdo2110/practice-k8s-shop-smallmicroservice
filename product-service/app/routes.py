"""HTTP layer product-service: CRUD danh mục sản phẩm (catalog).

Phân quyền bằng JWT ký từ auth-service (dùng chung JWT_SECRET) — không gọi
sang auth-service, nên auth sập thì đọc/ghi sản phẩm vẫn chạy (good for K8s demo).
"""
import re

from flask import Blueprint, jsonify, request

from . import repository as repo
from .errors import bad_request, not_found
from .security import require_role

products_bp = Blueprint("products", __name__)
catalog_bp = Blueprint("catalog", __name__)

CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
MAX_DESCRIPTION = 2000
MAX_URL = 512


def _int_arg(name, default, minimum, maximum):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise bad_request(f"Query '{name}' phải là số", code="QUERY_INVALID")
    return min(maximum, max(minimum, value))


def _str_field(data, name, max_length, required=False, default=""):
    value = data.get(name, default)
    if value is None:
        value = default
    if not isinstance(value, str):
        raise bad_request(f"Field '{name}' phải là chuỗi", code="FIELD_TYPE")
    value = value.strip()
    if required and not value:
        raise bad_request(f"Thiếu field '{name}'", code="FIELD_REQUIRED")
    if len(value) > max_length:
        raise bad_request(f"Field '{name}' tối đa {max_length} ký tự", code="FIELD_TOO_LONG")
    return value


def _number_field(data, name, required=False, minimum=0.0, maximum=1e12, integer=False, default=None):
    value = data.get(name, default)
    if value is None or value == "":
        if required:
            raise bad_request(f"Thiếu field '{name}'", code="FIELD_REQUIRED")
        return default
    try:
        number = int(value) if integer else float(value)
    except (TypeError, ValueError):
        raise bad_request(f"Field '{name}' phải là số", code="FIELD_TYPE")
    if number < minimum or number > maximum:
        raise bad_request(f"Field '{name}' phải trong [{minimum}, {maximum}]", code="FIELD_RANGE")
    return number


def _body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise bad_request("Body phải là JSON object", code="INVALID_JSON")
    return data


# --------------------------------------------------------------------------- list
@products_bp.get("")
@products_bp.get("/")
def list_products():
    page = _int_arg("page", 1, 1, 10_000)
    size = _int_arg("pageSize", 12, 1, 100)
    q = (request.args.get("q") or "").strip()[:120]
    category = (request.args.get("category") or "").strip().lower()
    sort = (request.args.get("sort") or "-created").strip()

    items, total = repo.search(q, category, sort, size, (page - 1) * size)
    return jsonify(
        {
            "data": items,
            "meta": {"page": page, "pageSize": size, "total": total, "q": q, "category": category, "sort": sort},
        }
    )


@catalog_bp.get("/categories")
def list_categories():
    return jsonify({"data": repo.categories()})


# ---------------------------------------------------------------------------- one
@products_bp.get("/<int:product_id>")
def get_product(product_id):
    product = repo.get_by_id(product_id)
    if not product:
        raise not_found(f"Không tìm thấy sản phẩm {product_id}", code="PRODUCT_NOT_FOUND")
    return jsonify({"data": product})


# ------------------------------------------------------------------------- create
@products_bp.post("")
@products_bp.post("/")
@require_role("admin")
def create_product():
    data = _body()
    name = _str_field(data, "name", 160, required=True)
    description = _str_field(data, "description", MAX_DESCRIPTION)
    price = _number_field(data, "price", required=True, minimum=0)
    stock = _number_field(data, "stock", integer=True, minimum=0, maximum=1_000_000, default=0)
    category = _str_field(data, "category", 64).lower() or "other"
    image_url = _str_field(data, "imageUrl", MAX_URL)
    if not CATEGORY_RE.match(category):
        raise bad_request("category chỉ dùng a-z0-9_-", code="CATEGORY_INVALID")

    product_id = repo.create(name, description, price, stock, category, image_url)
    return jsonify({"data": repo.get_by_id(product_id)}), 201


# ------------------------------------------------------------------------- update
@products_bp.put("/<int:product_id>")
@products_bp.patch("/<int:product_id>")
@require_role("admin")
def update_product(product_id):
    if not repo.get_by_id(product_id):
        raise not_found(f"Không tìm thấy sản phẩm {product_id}", code="PRODUCT_NOT_FOUND")

    data = _body()
    values = {}
    if "name" in data:
        values["name"] = _str_field(data, "name", 160, required=True)
    if "description" in data:
        values["description"] = _str_field(data, "description", MAX_DESCRIPTION)
    if "price" in data:
        values["price"] = _number_field(data, "price", required=True, minimum=0)
    if "stock" in data:
        values["stock"] = _number_field(data, "stock", required=True, integer=True, minimum=0, maximum=1_000_000)
    if "category" in data:
        category = _str_field(data, "category", 64, required=True).lower()
        if not CATEGORY_RE.match(category):
            raise bad_request("category chỉ dùng a-z0-9_-", code="CATEGORY_INVALID")
        values["category"] = category
    if "imageUrl" in data:
        values["imageUrl"] = _str_field(data, "imageUrl", MAX_URL)

    if not values:
        raise bad_request("Không có field nào để cập nhật", code="NOTHING_TO_UPDATE")

    repo.update(product_id, values)
    return jsonify({"data": repo.get_by_id(product_id)})


# ------------------------------------------------------------------------- delete
@products_bp.delete("/<int:product_id>")
@require_role("admin")
def delete_product(product_id):
    if not repo.soft_delete(product_id):
        raise not_found(f"Không tìm thấy sản phẩm {product_id}", code="PRODUCT_NOT_FOUND")
    return jsonify({"data": {"id": product_id, "deleted": True}})
