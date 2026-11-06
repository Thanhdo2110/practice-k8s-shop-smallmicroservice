"""Factory khởi tạo auth-service (Flask app)."""
import logging
import sys
import time
import uuid

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

from .config import Config
from .errors import ApiError


def _setup_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s", datefmt="%H:%M:%S"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))
    app.logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))


def _cors_headers(response):
    origin = request.headers.get("Origin", "")
    allowed = Config.CORS_ORIGINS
    if origin and (origin in allowed or "*" in allowed):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    # các header này cần có kể cả khi Origin không khớp, Ingress/CORS test dễ nhầm chỗ này
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Request-Id"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Max-Age"] = "600"
    return response


def create_app():
    app = Flask(Config.SERVICE_NAME)
    app.json.sort_keys = False
    _setup_logging(app)

    from .health import bp as health_bp
    from .routes import auth_bp, users_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")

    @app.before_request
    def _start():
        g.request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        g.started_at = time.monotonic()

    @app.after_request
    def _finish(response):
        if request.method == "OPTIONS":  # preflight
            response = app.make_response(("", 204))
        response.headers["X-Request-Id"] = g.get("request_id", "-")
        response.headers["X-Service"] = Config.SERVICE_NAME
        response = _cors_headers(response)
        cost = (time.monotonic() - getattr(g, "started_at", time.monotonic())) * 1000
        app.logger.info(
            "%s %s -> %s (%.1fms) ip=%s",
            request.method,
            request.full_path,
            response.status_code,
            cost,
            request.remote_addr,
        )
        return response

    @app.errorhandler(ApiError)
    def _on_api_error(error):
        app.logger.warning("ApiError %s %s: %s", error.status, error.code, error.message)
        return error.to_response()

    @app.errorhandler(HTTPException)
    def _on_http(error):
        code = error.name.upper().replace(" ", "_") if error.name else "HTTP_ERROR"
        return jsonify({"error": {"code": code, "message": error.description}}), error.code or 500

    @app.errorhandler(Exception)
    def _on_unexpected(error):
        app.logger.exception("Unhandled error: %s", error)
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Lỗi hệ thống, xem log của pod"}}), 500

    return app
