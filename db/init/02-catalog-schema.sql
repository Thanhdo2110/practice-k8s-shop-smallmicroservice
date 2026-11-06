-- =============================================================================
-- 02-catalog-schema.sql — schema + dữ liệu mẫu của product-service (shop_catalog)
-- =============================================================================

USE shop_catalog;

CREATE TABLE IF NOT EXISTS products (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name        VARCHAR(160)    NOT NULL,
    description TEXT            NULL,
    price       DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    stock       INT UNSIGNED    NOT NULL DEFAULT 0,
    category    VARCHAR(64)     NOT NULL DEFAULT 'other',
    image_url   VARCHAR(512)    NOT NULL DEFAULT '',
    deleted_at  TIMESTAMP       NULL DEFAULT NULL COMMENT 'soft delete',
    created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_products_category (category),
    KEY idx_products_price (price),
    KEY idx_products_deleted_at (deleted_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

INSERT INTO products (name, description, price, stock, category, image_url) VALUES
('Áo thun Basic Trắng',        'Cotton 100%, form rộng, fitsize M',            149000.00, 120, 'ao',         'https://picsum.photos/seed/aothun/400/400'),
('Áo Sơ Mi Nam Xanh Neon',     'Oxford lụa lạnh, tay dài, form slim',          289000.00,  60, 'ao',         'https://picsum.photos/seed/aoso/400/400'),
('Áo Khoác Gió Unisex',        'Chống nước nhẹ, có mũ, 2 túi trong',            399000.00,  35, 'ao',         'https://picsum.photos/seed/aokhoac/400/400'),
('Quần Jean Slim Fit Xanh Đậm','Denim 12oz, co giãn 2%, size 28-32',            329000.00,  80, 'quan',       'https://picsum.photos/seed/jean/400/400'),
('Quần Kaki Baggy Be',         'Kaki cotton, form baggy năng động',            259000.00,  45, 'quan',       'https://picsum.photos/seed/kaki/400/400'),
('Giày Sneaker Trắng Đế Cao',  'Da PU, đế 4cm, êm chân đi cả ngày',            549000.00,  25, 'giay',       'https://picsum.photos/seed/sneaker/400/400'),
('Giày Lười Da Nâu',           'Da thật, khâu tay, size 39-44',                689000.00,  18, 'giay',       'https://picsum.photos/seed/giaylui/400/400'),
('Dép Quai Ngang Đen',         'EVA nguyên khối, chống trượt',                  99000.00,  200, 'giay',       'https://picsum.photos/seed/dep/400/400'),
('Balo Laptop 15.6 inch',      'Chống nước, ngăn chống sốc, cổng USB',         429000.00,  40, 'phu-kien',   'https://picsum.photos/seed/balo/400/400'),
('Nón Lưỡi Trai Nomura',       'Cotton Canvas, thêu logo, dây dù',            129000.00,  150, 'phu-kien',   'https://picsum.photos/seed/non/400/400'),
('Đồng Hồ Quartz Dây Da',      'Machine Nhật, chống nước 3ATM',               1290000.00,  12, 'phu-kien',   'https://picsum.photos/seed/dongho/400/400'),
('Vớ Thể Thao (Hộp 5 Đôi)',    'Cotton thể thao, cổ trung',                    79000.00,  300, 'phu-kien',   'https://picsum.photos/seed/vo/400/400'),
('Tai Nghe Bluetooth TWS',     'ANC, pin 24h, chống nước IPX5',                790000.00,  30, 'cong-nghe',  'https://picsum.photos/seed/tainhe/400/400'),
('Sạc Dự Phòng 20000mAh',      'PD 22.5W, 2 cổng USB-C + 1 USB-A',             459000.00,  55, 'cong-nghe',  'https://picsum.photos/seed/sac/400/400'),
('Bàn Phím Cơ 68 Keys',        'Switch red, hotswap, LED RGB',                1190000.00,   9, 'cong-nghe',  'https://picsum.photos/seed/banphim/400/400'),
('Chuột Không Dây Ergo',       '2.4GHz + Bluetooth, 6 nút, pin 70 ngày',       359000.00,  70, 'cong-nghe',  'https://picsum.photos/seed/chuot/400/400');
