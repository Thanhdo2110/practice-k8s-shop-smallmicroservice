-- =============================================================================
-- 99-verify.sql — chạy khi container mysql khởi động xong để kiểm tra init đủ chưa
-- Manual: mysql -u root -p < db/init/99-verify.sql
-- =============================================================================

SELECT '=== databases ===' AS info;
SHOW DATABASES;

SELECT COUNT(*) AS users_total      FROM shop_auth.users;
SELECT COUNT(*) AS products_total,  SUM(stock) AS stock_total FROM shop_catalog.products WHERE deleted_at IS NULL;
SELECT category, COUNT(*) AS so_luong FROM shop_catalog.products GROUP BY category;
SELECT COUNT(*) AS orders_total     FROM shop_orders.orders;

SELECT '=== app users ===' AS info;
SELECT user, host FROM mysql.user WHERE user LIKE '%_user' ORDER BY user;
