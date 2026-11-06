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
            "endpoints": [
                "GET /healthz",
                "GET /readyz",
                "GET /api/v1/products",
                "GET /api/v1/products/{id}",
                "GET /api/v1/categories",
                "POST|PUT|DELETE /api/v1/products (role=admin)",
            ],
        }
    )


@bp.get("/healthz")
def liveness():
    return jsonify({"status": "ok", "service": Config.SERVICE_NAME, "version": Config.VERSION})


@bp.get("/readyz")
def readiness():
    info = db.health()
    body = {"service": Config.SERVICE_NAME, "status": "ready" if info["ok"] else "not-ready", "database": info}
    return jsonify(body), (200 if info["ok"] else 503)
