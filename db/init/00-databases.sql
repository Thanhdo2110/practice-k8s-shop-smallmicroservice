-- =============================================================================
-- 00-databases.sql
-- Tạo 3 database (mỗi microservice một schema riêng) + 3 user + grant.
-- Trên K8s: mount file này vào /docker-entrypoint-initdb.d/ của image mysql:8
-- (chỉ chạy khi data directory còn trống).
-- Mật khẩu ở đây là demo — khi thực hành hãy chuyển sang Kubernetes Secret.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS shop_auth    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS shop_catalog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS shop_orders  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


CREATE USER IF NOT EXISTS 'auth_user'@'%'    IDENTIFIED BY 'auth_password';
CREATE USER IF NOT EXISTS 'catalog_user'@'%' IDENTIFIED BY 'catalog_password';
CREATE USER IF NOT EXISTS 'orders_user'@'%'  IDENTIFIED BY 'orders_password';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON shop_auth.*    TO 'auth_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON shop_catalog.* TO 'catalog_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON shop_orders.*  TO 'orders_user'@'%';

FLUSH PRIVILEGES;

-- Kiểm tra nhanh:
--   SHOW DATABASES;
--   SELECT user, host FROM mysql.user;
