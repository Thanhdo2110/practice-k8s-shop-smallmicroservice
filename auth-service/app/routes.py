"""HTTP layer: /api/v1/auth/* và /api/v1/users/*.

Response envelope thống nhất 3 service:
    thành công -> {"data": ..., "meta": ...?}
    lỗi        -> {"error": {"code": ..., "message": ..., "details": ...?}}
"""
import re

from flask import Blueprint, g, jsonify, request

from . import repository as repo
from .errors import bad_request, conflict, not_found, unauthorized
from .security import hash_password, issue_token, require_auth, require_role, verify_password

auth_bp = Blueprint("auth", __name__)
users_bp = Blueprint("users", __name__)

USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,32}$")
PASSWORD_MIN = 8
PASSWORD_MAX = 72  # giữ tương thích nếu bạn đổi sang bcrypt


def _body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise bad_request("Body phải là JSON object", code="INVALID_JSON")
    return data


def _field(data, name, max_length, required=True):
    value = data.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise bad_request(f"Thiếu field '{name}'", code="FIELD_REQUIRED")
        return ""
    if not isinstance(value, str):
        raise bad_request(f"Field '{name}' phải là chuỗi", code="FIELD_TYPE")
    value = value.strip()
    if len(value) > max_length:
        raise bad_request(f"Field '{name}' tối đa {max_length} ký tự", code="FIELD_TOO_LONG")
    return value


def _int_arg(name, default, minimum, maximum):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise bad_request(f"Query '{name}' phải là số", code="QUERY_INVALID")
    return min(maximum, max(minimum, value))


# --------------------------------------------------------------------------- auth
@auth_bp.get("/ping")
def ping():
    return jsonify({"data": {"service": "auth", "pong": True}})


@auth_bp.post("/register")
def register():
    data = _body()
    username = _field(data, "username", 32).lower()
    email = _field(data, "email", 255).lower()
    password = _field(data, "password", PASSWORD_MAX)
    full_name = _field(data, "fullName", 128, required=False)

    if not USERNAME_RE.match(username):
        raise bad_request("Username 3-32 ký tự, chỉ chữ thường/số/._", code="USERNAME_INVALID")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", email):
        raise bad_request("Email không hợp lệ", code="EMAIL_INVALID")
    if len(password) < PASSWORD_MIN:
        raise bad_request(f"Mật khẩu tối thiểu {PASSWORD_MIN} ký tự", code="PASSWORD_WEAK")
    if repo.exists_username(username):
        raise conflict("Username đã tồn tại", code="USERNAME_TAKEN")
    if repo.exists_email(email):
        raise conflict("Email đã tồn tại", code="EMAIL_TAKEN")

    # user đầu tiên là admin -> khỏi seed hash mật khẩu trong db/init
    bootstrap_admin = repo.count_all() == 0
    role = "admin" if bootstrap_admin else "customer"
    user_id = repo.create(username, email, full_name, hash_password(password), role)
    return jsonify({"data": repo.find_by_id(user_id), "meta": {"bootstrapAdmin": bootstrap_admin}}), 201


@auth_bp.post("/login")
def login():
    data = _body()
    identifier = _field(data, "username", 255).lower()
    password = _field(data, "password", PASSWORD_MAX)

    user = repo.find_login_identity(identifier)
    if not user or not verify_password(user.pop("passwordHash", ""), password):
        # không tiết lộ tài khoản có tồn tại hay không
        raise unauthorized("Sai tài khoản hoặc mật khẩu", code="INVALID_CREDENTIALS")
    if not user["isActive"]:
        raise unauthorized("Tài khoản đã bị khoá", code="ACCOUNT_DISABLED")

    token, expires_at = issue_token(user)
    return jsonify(
        {
            "data": {
                "accessToken": token,
                "tokenType": "Bearer",
                "expiresAt": expires_at,
                "user": user,
            }
        }
    )


@auth_bp.get("/me")
@require_auth
def me():
    user = repo.find_by_id(g.user["id"])
    if not user:
        raise not_found("User không còn tồn tại", code="USER_GONE")
    return jsonify({"data": user})


# -------------------------------------------------------------------------- users
@users_bp.get("")
@users_bp.get("/")
@require_role("admin")
def list_users():
    page = _int_arg("page", 1, 1, 10_000)
    size = _int_arg("pageSize", 20, 1, 100)
    items = repo.list_page(size, (page - 1) * size)
    return jsonify({"data": items, "meta": {"page": page, "pageSize": size, "total": repo.count_all()}})


@users_bp.get("/<int:user_id>")
@require_role("admin")
def get_user(user_id):
    user = repo.find_by_id(user_id)
    if not user:
        raise not_found("Không tìm thấy user", code="USER_NOT_FOUND")
    return jsonify({"data": user})
