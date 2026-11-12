"""Truy cập MySQL bằng PyMySQL thuần (không ORM) — mỗi request một connection.

Lý do đơn giản hoá: khi thực hành K8s bạn cần đọc log/trace nhanh, ít tầng.
Bài tập mở rộng: thay bằng DBUtils.PooledDB rồi so sánh số connection MySQL
với `max_connections` khi scale replica lên 10.
"""
import decimal
import time
from contextlib import contextmanager
from datetime import date, datetime, time as dt_time
from functools import wraps

import pymysql
from pymysql.cursors import DictCursor

from .config import Config
from .errors import ApiError, conflict, upstream_failure


def _connect(ping=False):
    read_timeout = Config.DB_PING_TIMEOUT if ping else 10

    ssl_args = None
    if Config.MYSQL_SSL_CA:
        ssl_args = {
            "ca": Config.MYSQL_SSL_CA,
            "check_hostname": True,
        }

    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=Config.DB_CONNECT_TIMEOUT,
        read_timeout=read_timeout,
        write_timeout=read_timeout,
        ssl=ssl_args,
    )


def _clean(value):
    """Decimal/DATE không nằm trong default JSON provider của Flask."""
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, (date, dt_time)):
        return value.isoformat()
    return value


def _row(row):
    """Không tự đổi tên cột: muốn camelCase trong JSON thì alias ngay trong SQL
    (SELECT full_name AS fullName) — dễ trace khi đọc log hơn."""
    return {k: _clean(v) for k, v in row.items()} if row else row


def _short(exc):
    args = getattr(exc, "args", ())
    text = " ".join(str(a) for a in args[:2]) if args else str(exc)
    return f"{type(exc).__name__}: {text}"[:200]


def _translate(exc):
    if isinstance(exc, pymysql.err.IntegrityError):
        return conflict("Dữ liệu trùng khoá duy nhất", code="DUPLICATE_KEY", details=_short(exc))
    if isinstance(exc, pymysql.err.ProgrammingError):
        return ApiError(500, "DB_QUERY_ERROR", _short(exc))
    if isinstance(exc, RuntimeError) and "cryptography" in str(exc):
        # MySQL 8 dùng caching_sha2_password; PyMySQL cần extra [rsa] để ký RSA
        return upstream_failure(
            "Thiếu package 'cryptography' cho auth caching_sha2_password — cài PyMySQL[rsa]",
            code="DB_AUTH_PLUGIN",
        )
    if isinstance(exc, (pymysql.err.OperationalError, pymysql.err.InterfaceError, OSError)):
        return upstream_failure(
            "MySQL không phản hồi",
            details={"database": Config.MYSQL_DATABASE, "error": _short(exc)},
        )
    return None


def _guard(func):
    """Dịch lỗi pymysql sang ApiError có code rõ — DB sập trả 503 DB_UNAVAILABLE
    thay vì 500 INTERNAL_ERROR chung chung."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            translated = _translate(exc)
            if translated:
                raise translated from exc
            raise

    return wrapper


@contextmanager
def connection():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction():
    """Dùng khi cần ghi nhiều bảng atomically (orders + order_items)."""
    conn = None
    try:
        conn = _connect()
        conn.autocommit(False)
        yield conn
        conn.commit()
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        raise (_translate(exc) or exc) from exc
    finally:
        if conn is not None:
            conn.close()


@_guard
def fetch_all(sql, params=()):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return [_row(r) for r in cur.fetchall()]


@_guard
def fetch_one(sql, params=()):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return _row(row) if row else None


@_guard
def insert_returning_id(sql, params=()):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid


@_guard
def execute(sql, params=()):
    """Trả về số dòng bị ảnh hưởng."""
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def health():
    """Cho /readyz: ok + latency + thông tin lỗi ngắn gọn."""
    started = time.monotonic()
    info = {"ok": False, "database": Config.MYSQL_DATABASE, "host": f"{Config.MYSQL_HOST}:{Config.MYSQL_PORT}"}
    try:
        conn = _connect(ping=True)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT VERSION() AS v")
                info["serverVersion"] = (cur.fetchone() or {}).get("v")
        finally:
            conn.close()
        info["ok"] = True
    except Exception as exc:  # pymysql raise nhiều loại, gom hết để probe không sập
        info["error"] = f"{type(exc).__name__}: {exc}"[:200]
    info["latencyMs"] = round((time.monotonic() - started) * 1000, 1)
    return info
