"""Endpoint sống/chín của service — dùng cho liveness/readiness/startup probe.

- /healthz : process còn sống, KHÔNG chạm DB  => livenessProbe
- /readyz  : MySQL connect được               => readinessProbe / startupProbe
"""
from flask import Blueprint, jsonify

from . import db
from .config import Config

bp = Blueprint("health", __name__)


@bp.get("/")
def index():
    return jsonify(
        {
            "service": Config.SERVICE_NAME,
            "version": Config.VERSION,
            "database": Config.MYSQL_DATABASE,
            "upstream": {"productService": Config.PRODUCT_SERVICE_BASE_URL},
            "endpoints": [
                "GET /healthz",
                "GET /readyz",
                "POST /api/v1/orders",
                "GET /api/v1/orders",
                "GET /api/v1/orders/{id}",
                "POST /api/v1/orders/{id}/cancel",
            ],
        }
    )


@bp.get("/healthz")
def liveness():
    return jsonify({"status": "ok", "service": Config.SERVICE_NAME, "version": Config.VERSION})


@bp.get("/readyz")
def readiness():
    """CHỈ phụ thuộc MySQL. Không check product-service ở đây: readiness mà
    phụ thuộc downstream thì một service lỗi sẽ làm cả chuỗi mất ready (domino).
    Muốn xem state upstream: GET / (không gọi HTTP, chỉ in cấu hình)."""
    info = db.health()
    body = {"service": Config.SERVICE_NAME, "status": "ready" if info["ok"] else "not-ready", "database": info}
    return jsonify(body), (200 if info["ok"] else 503)
