"""Password hash + JWT HS256.

Mọi service dùng chung JWT_SECRET nên tự verify token được,
không cần gọi lại auth-service (sync-free). Secret này để trong Secret K8s.
"""
from functools import wraps

import time

import jwt
from werkzeug.security import check_password_hash, generate_password_hash
from flask import g, request

from .config import Config
from .errors import forbidden, unauthorized

ALGORITHM = "HS256"


def hash_password(plain):
    return generate_password_hash(plain)


def verify_password(stored_hash, plain):
    if not stored_hash:
        return False
    try:
        return check_password_hash(stored_hash, plain)
    except AttributeError:
        return False


def issue_token(user):
    """user: dict có id/username/role. Trả về (token, exp_unix)."""
    now = int(time.time())
    exp = now + Config.JWT_EXPIRE_SECONDS
    payload = {
        "sub": str(user["id"]),
        "uid": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iss": Config.JWT_ISSUER,
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm=ALGORITHM)
    return token, exp


def decode_token(token):
    try:
        return jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=[ALGORITHM],
            issuer=Config.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise unauthorized("Token đã hết hạn, đăng nhập lại", code="TOKEN_EXPIRED")
    except jwt.PyJWTError:
        raise unauthorized("Token không hợp lệ", code="TOKEN_INVALID")


def bearer_token():
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = bearer_token()
        if not token:
            raise unauthorized("Thiếu header Authorization: Bearer <token>", code="TOKEN_MISSING")
        claims = decode_token(token)
        g.user = {
            "id": int(claims.get("uid") or claims["sub"]),
            "username": claims.get("username", ""),
            "role": claims.get("role", "customer"),
        }
        return func(*args, **kwargs)

    return wrapper


def require_role(*roles):
    def decorator(func):
        @wraps(func)
        @require_auth
        def wrapper(*args, **kwargs):
            if g.user["role"] not in roles:
                raise forbidden("Cần quyền: " + "/".join(roles), code="ROLE_DENIED")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def current_user():
    return g.get("user")
