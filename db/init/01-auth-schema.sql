-- =============================================================================
-- 01-auth-schema.sql — schema riêng của auth-service (database shop_auth)
-- Không seed user: user đầu tiên đăng ký sẽ tự nhận role=admin
-- (xem auth-service/app/routes.py) -> khỏi phải lưu hash mật khẩu trong SQL.
-- =============================================================================

USE shop_auth;

CREATE TABLE IF NOT EXISTS users (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username      VARCHAR(64)     NOT NULL,
    email         VARCHAR(255)    NOT NULL,
    full_name     VARCHAR(128)    NOT NULL DEFAULT '',
    password_hash VARCHAR(255)    NOT NULL COMMENT 'werkzeug pbkdf2:sha256',
    role          ENUM('customer','admin') NOT NULL DEFAULT 'customer',
    is_active     TINYINT(1)      NOT NULL DEFAULT 1,
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email),
    KEY idx_users_role (role)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
