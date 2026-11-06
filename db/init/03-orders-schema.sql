-- =============================================================================
-- 03-orders-schema.sql — schema riêng của order-service (database shop_orders)
--
-- Để ý: order_items lưu SNAPSHOT product_name / unit_price tại thời điểm đặt.
-- Đây là quan hệ "logic" chứ không phải FK liên database — đúng tư tưởng
-- microservices: mỗi service tự sở hữu dữ liệu của mình, không JOIN sang
-- shop_catalog. Muốn biết giá hiện tại thì order-service gọi HTTP sang
-- product-service (xem order-service/app/catalog_client.py).
-- =============================================================================

USE shop_orders;

CREATE TABLE IF NOT EXISTS orders (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id      BIGINT UNSIGNED NOT NULL,
    username     VARCHAR(64)     NOT NULL DEFAULT '',
    status       ENUM('pending','paid','cancelled','done') NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    note         VARCHAR(255)    NOT NULL DEFAULT '',
    created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_orders_user (user_id, created_at),
    KEY idx_orders_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_items (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id     BIGINT UNSIGNED NOT NULL,
    product_id   BIGINT UNSIGNED NOT NULL,
    product_name VARCHAR(160)    NOT NULL DEFAULT '',
    unit_price   DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    quantity     INT UNSIGNED    NOT NULL DEFAULT 1,
    subtotal     DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_items_order (order_id),
    KEY idx_items_product (product_id),
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
