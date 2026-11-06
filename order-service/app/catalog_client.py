"""Gọi product-service qua HTTP — đây là chỗ Cluster DNS của K8s thể hiện vai trò.

PRODUCT_SERVICE_BASE_URL khi ở trong cluster: http://product-service:8001
(khác namespace: http://product-service.<namespace>.svc.cluster.local:8001)

Timeout ngắn + đúng 1 retry: trong lúc rolling update, Service vẫn còn endpoint
nhưng pod mới chưa ready -> retry lần 2 thường ăn được pod đã ready.
"""
import logging
import time

import requests

from .config import Config
from .errors import upstream_failure

log = logging.getLogger(__name__)

_session = requests.Session()
_session.headers.update({"Accept": "application/json", "User-Agent": f"order-service/{Config.VERSION}"})
_RETRIES = 2


def _base():
    return Config.PRODUCT_SERVICE_BASE_URL.rstrip("/")


def fetch_product(product_id, request_id=""):
    """Return: dict sản phẩm | None (404) | raise ApiError 503 (upstream không trả lời)."""
    headers = {"X-Request-Id": request_id} if request_id else None
    last_error = None
    for attempt in range(1, _RETRIES + 1):
        started = time.monotonic()
        try:
            response = _session.get(
                f"{_base()}/api/v1/products/{product_id}",
                headers=headers,
                timeout=Config.PRODUCT_SERVICE_TIMEOUT,
            )
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            log.warning("product-service call %s (attempt %s) failed: %s", product_id, attempt, last_error)
            continue

        cost = round((time.monotonic() - started) * 1000, 1)
        if response.status_code == 404:
            return None
        if not response.ok:
            last_error = f"HTTP {response.status_code}"
            log.warning("product-service %s -> %s (%sms)", product_id, response.status_code, cost)
            continue
        try:
            body = response.json()
        except ValueError:
            last_error = "product-service trả body không phải JSON"
            continue
        log.info("product-service %s -> %s (%sms)", product_id, response.status_code, cost)
        return (body or {}).get("data")

    raise upstream_failure(
        "Không gọi được product-service",
        details={"baseUrl": _base(), "lastError": last_error, "attempts": _RETRIES},
    )
