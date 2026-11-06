"""Lỗi thống nhất dạng JSON: {"error": {"code", "message", "details"?}}."""


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details

    def to_response(self):
        from flask import jsonify

        body = {"error": {"code": self.code, "message": self.message}}
        if self.details:
            body["error"]["details"] = self.details
        return jsonify(body), self.status


def bad_request(message, code="BAD_REQUEST", details=None):
    return ApiError(400, code, message, details)


def unauthorized(message, code="UNAUTHORIZED"):
    return ApiError(401, code, message)


def forbidden(message, code="FORBIDDEN"):
    return ApiError(403, code, message)


def not_found(message, code="NOT_FOUND"):
    return ApiError(404, code, message)


def conflict(message, code="CONFLICT"):
    return ApiError(409, code, message)


def upstream_failure(message, details=None, code="UPSTREAM_ERROR"):
    """Service khác / MySQL trả lỗi — 502/503 giúp probe và log dễ phân biệt."""
    return ApiError(503, code, message, details)
