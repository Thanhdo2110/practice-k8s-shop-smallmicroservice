"""Cấu hình đọc từ environment; nếu có file `.env` trong thư mục service thì nạp thêm.

Local:  cp .env.example .env
K8s:    không cần .env — môi trường đến từ ConfigMap + Secret (envFrom/valueFrom).
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv(path=None):
    """Đọc .env kiểu KEY=VALUE tối giản, không thêm dependency. Biến đã tồn tại thắng."""
    path = path or os.path.join(os.path.dirname(_HERE), ".env")
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_dotenv()


def _int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _csv(name: str, default: str) -> list:
    raw = os.getenv(name) or default
    return [item.strip() for item in raw.split(",") if item.strip()]


class Config:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "auth-service")
    VERSION = os.getenv("APP_VERSION", "1.0.0")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = _int("PORT", 8000)
    LOG_LEVEL = (os.getenv("LOG_LEVEL") or "INFO").upper()

    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = _int("MYSQL_PORT", 3306)
    MYSQL_USER = os.getenv("MYSQL_USER", "auth_user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "auth_password")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "shop_auth")
    DB_CONNECT_TIMEOUT = _int("DB_CONNECT_TIMEOUT", 3)
    DB_PING_TIMEOUT = _int("DB_PING_TIMEOUT", 3)
    MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "").strip()

    JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me")
    JWT_ISSUER = os.getenv("JWT_ISSUER", "shop")
    JWT_EXPIRE_SECONDS = _int("JWT_EXPIRE_SECONDS", 86400)

    CORS_ORIGINS = _csv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
