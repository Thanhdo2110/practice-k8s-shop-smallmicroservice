"""Layer SQL của auth-service — chỉ service này được chạm bảng `users` (shop_auth)."""
from . import db

COLUMNS = (
    "id, username, email, full_name AS fullName, role, "
    "is_active AS isActive, created_at AS createdAt, updated_at AS updatedAt"
)


def count_all():
    row = db.fetch_one("SELECT COUNT(*) AS total FROM users")
    return int(row["total"]) if row else 0


def exists_username(username):
    return bool(db.fetch_one("SELECT 1 AS one FROM users WHERE username = %s", (username,)))


def exists_email(email):
    return bool(db.fetch_one("SELECT 1 AS one FROM users WHERE email = %s", (email,)))


def find_by_id(user_id):
    return db.fetch_one("SELECT " + COLUMNS + " FROM users WHERE id = %s", (user_id,))


def find_login_identity(identifier):
    """identifier là username HOẶC email; có cả password_hash để verify."""
    return db.fetch_one(
        "SELECT " + COLUMNS + ", password_hash AS passwordHash "
        "FROM users WHERE username = %s OR email = %s LIMIT 1",
        (identifier, identifier),
    )


def create(username, email, full_name, password_hash, role):
    return db.insert_returning_id(
        "INSERT INTO users (username, email, full_name, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
        (username, email, full_name, password_hash, role),
    )


def set_active(user_id, is_active):
    return db.execute("UPDATE users SET is_active = %s WHERE id = %s", (int(bool(is_active)), user_id))


def list_page(limit, offset):
    return db.fetch_all(
        "SELECT " + COLUMNS + " FROM users ORDER BY id DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )
