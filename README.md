# Shop K8s — project microservices để thực hành Kubernetes

Demo bán hàng gồm 4 thành phần độc lập, mỗi cái build image riêng:


| Thành phần        | Công nghệ       | Port mặc định           | Database riêng  |
| ----------------- | --------------- | ----------------------- | --------------- |
| `frontend`        | React 18 + Vite | 5173 (dev) / 80 (nginx) | —               |
| `auth-service`    | Python Flask    | 8000                    | `shop_auth`     |
| `product-service` | Python Flask    | 8001                    | `shop_catalog`  |
| `order-service`   | Python Flask    | 8002                    | `shop_orders`   |
| `mysql`           | MySQL 8         | 3306                    | 3 schema ở trên |


Mỗi service sở hữu schema riêng theo đúng tư tưởng microservices: **không service nào đọc bảng của service khác**. `order-service` muốn biết giá sản phẩm phải gọi HTTP sang `product-service` — đó chính là chỗ bạn thực hành service discovery bằng Cluster DNS, timeout, retry và NetworkPolicy.

> Project này **không có Dockerfile và không có manifest Kubernetes** — phần đó bạn tự viết.



## Cấu trúc thư mục

```text
ProjectThucHanhK8s/
├── README.md
├── .gitignore
├── db/init/                     # mount vào /docker-entrypoint-initdb.d của image mysql:8
│   ├── 00-databases.sql         # tạo 3 database + 3 user + grant
│   ├── 01-auth-schema.sql
│   ├── 02-catalog-schema.sql    # schema + 16 sản phẩm mẫu
│   ├── 03-orders-schema.sql
│   └── 99-verify.sql
├── auth-service/                # Flask: register / login / JWT / danh sách user
│   ├── app/{__init__,config,db,errors,health,repository,routes,security}.py
│   ├── requirements.txt  wsgi.py  .env.example
├── product-service/             # Flask: CRUD catalog + categories
│   └── (cấu trúc như trên)
├── order-service/               # Flask: đơn hàng, gọi sang product-service
│   └── (cấu trúc như trên, thêm app/catalog_client.py)
└── frontend/                    # React + Vite
    ├── src/{api,components,context,lib,pages}/
    ├── index.html  vite.config.js  package.json  .env.example
```

Ba service Python trùng nhau `config.py`, `db.py`, `errors.py`, `health.py`, `security.py` — **có chủ đích**: mỗi service phải standalone để build image riêng, không có package dùng chung.

## Response envelope (cả 3 service giống nhau)

```json
{ "data": {}, "meta": { "page": 1, "pageSize": 12, "total": 16 } }
{ "error": { "code": "TOKEN_EXPIRED", "message": "...", "details": {} } }
```

`code` là chuỗi ổn định để frontend map thông báo. Mọi response đều có header `X-Request-Id` (frontend sinh ra và truyền sang từng service) — rất tiện khi `kubectl logs -f` nhiều pod cùng lúc.


| Code                                                                                                                                                                                                                                            | HTTP | Khi nào                                     |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ------------------------------------------- |
| `FIELD_REQUIRED`, `FIELD_TYPE`, `FIELD_TOO_LONG`, `FIELD_RANGE`, `INVALID_JSON`, `SORT_INVALID`, `CATEGORY_INVALID`, `ITEMS_REQUIRED`, `ITEM_INVALID`, `QUANTITY_RANGE`, `TOO_MANY_ITEMS`, `USERNAME_INVALID`, `EMAIL_INVALID`, `PASSWORD_WEAK` | 400  | payload/query sai                           |
| `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED`, `INVALID_CREDENTIALS`, `ACCOUNT_DISABLED`                                                                                                                                                    | 401  | auth                                        |
| `ROLE_DENIED`, `ORDER_FORBIDDEN`                                                                                                                                                                                                                | 403  | thiếu quyền admin / không phải chủ đơn      |
| `PRODUCT_NOT_FOUND`, `ORDER_NOT_FOUND`, `USER_NOT_FOUND`                                                                                                                                                                                        | 404  | không tồn tại                               |
| `USERNAME_TAKEN`, `EMAIL_TAKEN`, `DUPLICATE_KEY`, `CANCEL_NOT_ALLOWED`                                                                                                                                                                          | 409  | xung đột dữ liệu/trạng thái                 |
| `DB_UNAVAILABLE`, `DB_AUTH_PLUGIN`, `UPSTREAM_ERROR`                                                                                                                                                                                            | 503  | MySQL hoặc service downstream không trả lời |




## Health endpoint (dùng cho probe)

- `GET /healthz` — liveness. Luôn 200 khi process còn sống, **không** chạm DB.
- `GET /readyz` — readiness. Connect MySQL + `SELECT VERSION()` (timeout `DB_PING_TIMEOUT`), không được thì trả 503.
- `GET /` — tên service, version, DB, upstream (riêng order-service), danh sách endpoint.

`order-service` **cố ý không** check `product-service` trong `/readyz`: readiness mà phụ thuộc downstream thì một service lỗi sẽ làm cả chuỗi mất ready.

## 1. Chạy local (chưa cần K8s)

Cần Python 3.10+, Node 18+, MySQL 8 ở `127.0.0.1:3306`.

```bash
# 1) Tạo database + user + schema + dữ liệu mẫu
mysql -u root -p < db/init/00-databases.sql
mysql -u root -p < db/init/01-auth-schema.sql
mysql -u root -p < db/init/02-catalog-schema.sql
mysql -u root -p < db/init/03-orders-schema.sql
mysql -u root -p < db/init/99-verify.sql

# 2) Mỗi service một terminal
cd auth-service
python -m venv .venv
source .venv/Scripts/activate          # Windows CMD: .venv\Scripts\activate.bat
pip install -r requirements.txt
cp .env.example .env
python wsgi.py                         # nghe ở 0.0.0.0:8000

cd ../product-service                  # tương tự, .env đã có PORT=8001
cd ../order-service                    # tương tự, .env có PORT=8002 + PRODUCT_SERVICE_BASE_URL

# 3) Frontend
cd frontend
npm install
npm run dev                            # http://localhost:5173, Vite proxy san sang 3 backend
```

`app/config.py` của mỗi service tự nạp file `.env` đặt ngay trong thư mục service (không cần python-dotenv); biến đã có trong môi trường sẽ thắng. Khi lên K8s không dùng `.env` — env đến từ ConfigMap + Secret. Frontend không cần `.env.local` vì mặc định `VITE_API_BASE_URL` rỗng là đúng ý.

## 2. Biến môi trường


| Env                                     | Ý nghĩa                                             | Gợi ý trong K8s                                          |
| --------------------------------------- | --------------------------------------------------- | -------------------------------------------------------- |
| `HOST`                                  | bind address, code default `0.0.0.0`                | `0.0.0.0`; nếu chạy gunicorn thì `--bind 0.0.0.0:$PORT`  |
| `PORT`                                  | port Flask/gunicorn listen                          | `8000` / `8001` / `8002`                                 |
| `MYSQL_HOST`                            | host MySQL                                          | `mysql` hoặc `mysql.<namespace>.svc.cluster.local`       |
| `MYSQL_PORT`                            |                                                     | `3306`                                                   |
| `MYSQL_USER`                            | user riêng của từng service                         | `auth_user` / `catalog_user` / `orders_user`             |
| `MYSQL_PASSWORD`                        | **để trong Secret**, không nhét vào ConfigMap       | `auth_password` / `catalog_password` / `orders_password` |
| `MYSQL_DATABASE`                        | schema                                              | `shop_auth` / `shop_catalog` / `shop_orders`             |
| `DB_CONNECT_TIMEOUT`, `DB_PING_TIMEOUT` | timeout connect / probe (giây)                      | `3`                                                      |
| `JWT_SECRET`                            | khóa HS256 — **cả 3 service dùng chung một Secret** | `openssl rand -hex 32`                                   |
| `JWT_ISSUER`                            | claim `iss`, 3 service phải trùng                   | `shop`                                                   |
| `JWT_EXPIRE_SECONDS`                    | TTL token                                           | `86400`                                                  |
| `LOG_LEVEL`                             | `DEBUG`/`INFO`/`WARNING`                            | `INFO`                                                   |
| `CORS_ORIGINS`                          | danh sách origin, phân cách dấu `,`                 | `http://localhost:5173`                                  |
| `PRODUCT_SERVICE_BASE_URL`              | chỉ `order-service` dùng                            | `http://product-service:8001`                            |
| `PRODUCT_SERVICE_TIMEOUT`               | timeout gọi liên service (giây)                     | `3`                                                      |
| `MAX_ITEMS_PER_ORDER`                   | số dòng sản phẩm tối đa/đơn                         | `20`                                                     |
| `SERVICE_NAME`, `APP_VERSION`           | hiện trong `/healthz` và log                        | theo service                                             |


Frontend: `VITE_API_BASE_URL` để trống nghĩa là gọi same-origin theo `/api/v1/...` (dev dùng Vite proxy, cluster dùng Ingress). Chỉ đặt giá trị khác khi bạn expose mỗi service một host riêng.

## 3. Tên Service K8s mà code đã giả định

```text
http://auth-service:8000
http://product-service:8001
http://order-service:8002
mysql:3306
```

`order-service` gọi `GET {PRODUCT_SERVICE_BASE_URL}/api/v1/products/{id}` để lấy giá và tồn kho. Khác namespace thì dùng `product-service.<namespace>.svc.cluster.local:8001`.

## 4. Test API bằng curl

```bash
# user đầu tiên đăng ký sẽ tự nhận role=admin (không cần seed hash mật khẩu trong SQL)
curl -s -X POST localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' \
  -d '{"username":"admin","email":"admin@shop.local","password":"matkhau123","fullName":"Quan Tri"}'

TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"matkhau123"}' | sed -n 's/.*"accessToken":"\([^"]*\)".*/\1/p')

curl -s localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8001/api/v1/products/?page=1&pageSize=5&q=ao&category=ao&sort=-price"
curl -s -X POST localhost:8001/api/v1/products/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ao Mua K8s","description":"test ghi","price":99000,"stock":10,"category":"ao","imageUrl":""}'
curl -s -X POST localhost:8002/api/v1/orders/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"items":[{"productId":1,"quantity":2}],"note":"thuc hanh"}'
curl -s "localhost:8002/api/v1/orders/?scope=all" -H "Authorization: Bearer $TOKEN"
```

Bảng endpoint:

```text
auth-service      GET  /api/v1/auth/ping
                  POST /api/v1/auth/register | /api/v1/auth/login
                  GET  /api/v1/auth/me                     (Bearer)
                  GET  /api/v1/users/, /api/v1/users/{id}  (admin)

product-service   GET  /api/v1/products/?page&pageSize&q&category&sort   (public)
                  GET  /api/v1/products/{id}                             (public)
                  GET  /api/v1/categories                                (public)
                  POST /api/v1/products/                                 (admin)
                  PUT|PATCH /api/v1/products/{id}                        (admin)
                  DELETE /api/v1/products/{id}                           (admin, soft delete)

order-service     POST /api/v1/orders/                     {items:[{productId,quantity}],note}
                  GET  /api/v1/orders/?page&pageSize&scope=mine|all
                  GET  /api/v1/orders/{id}
                  POST /api/v1/orders/{id}/cancel
```

`sort` của product-service: `created|price|name|stock`, thêm `-` để giảm dần (mặc định `-created`). Ghi (POST/PUT/DELETE) cần `role=admin`; đơn hàng luôn gắn `user_id` lấy từ JWT, khách chỉ xem/huỷ đơn của mình.

Trong cluster, thay `localhost` bằng `kubectl -n <namespace> port-forward svc/auth-service 8000:8000` (tương tự 8001, 8002).

## 5. Gợi ý lộ trình thực hành (manifest bạn tự viết)

1. `Namespace` + `ResourceQuota` + `LimitRange`.
2. MySQL: thử `Deployment` 1 replica rồi chuyển sang `StatefulSet` + `volumeClaimTemplates`; `Secret` cho `MYSQL_ROOT_PASSWORD` và mật khẩu app; `Service` ClusterIP; mount `db/init` vào `/docker-entrypoint-initdb.d`. Cố tình bỏ PVC rồi restart pod để thấy mất data và init SQL chạy lại.
3. `ConfigMap` cho env không nhạy cảm + `Secret` (`stringData`) cho `MYSQL_PASSWORD`, `JWT_SECRET`; gắn bằng `envFrom` và `valueFrom.secretKeyRef`.
4. `Deployment` 3 backend: `startupProbe`/`readinessProbe: /readyz`, `livenessProbe: /healthz`, `resources.requests/limits`, `terminationGracePeriodSeconds` + `preStop sleep`, `strategy.rollingUpdate.maxSurge/maxUnavailable`.
5. `Service` ClusterIP cho từng backend; `kubectl exec` vào pod `order-service` gọi `curl http://product-service:8001/healthz` để verify Cluster DNS; thử đặt sai tên DNS rồi đọc log.
6. Frontend build static serve bằng nginx; `Ingress` route `/` → frontend, `/api/v1/auth|users` → auth, `/api/v1/products|categories` → product, `/api/v1/orders` → order.
7. `HorizontalPodAutoscaler` v2 theo CPU cho `product-service` (bắt buộc có `requests.cpu`), tạo tải bằng pod busybox `wget` vòng lặp vào `/api/v1/products/`.
8. `PodDisruptionBudget`, `NetworkPolicy` (chỉ cho `order-service` gọi `product-service` + MySQL), `ServiceAccount` với `automountServiceAccountToken: false`, `securityContext` non-root.
9. Vận hành: `rollout status/history/undo`, `scale`, `logs -f --previous`, `kubectl debug`, `top pod`, `cordon` + `delete pod` để xem self-healing.



## 6. Lỗi thường gặp

- Bind `127.0.0.1` trong container (`flask --host` / `gunicorn --bind`) → probe không kết nối được, pod luôn NotReady. Luôn dùng `0.0.0.0`.
- `livenessProbe` trỏ vào `/readyz` → MySQL nháy một cái là kubelet kill pod, CrashLoopBackOff. Liveness chỉ dùng `/healthz`.
- Readiness fail liên tục vì MySQL chưa khởi động xong → thêm `startupProbe` với `failureThreshold` cao.
- Quên PVC cho `/var/lib/mysql` → mất đơn hàng khi pod restart.
- `ConfigMap` chứa `.sql`: key phải là tên file thuần (`00-databases.sql`); nếu mount bằng `subPath` thì file **không** tự cập nhật khi ConfigMap thay đổi.
- `JWT_SECRET` lệch nhau giữa các service → `order-service` trả `TOKEN_INVALID` với token hợp lệ của `auth-service`.
- Thiếu `cryptography` trong image → PyMySQL báo `RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods` khi connect MySQL 8. requirements ở đây đã dùng `PyMySQL[rsa]` để kéo nó vào.
- Truyền `VITE_API_BASE_URL` bằng `kubectl set env` cho Deployment frontend: không tác dụng, giá trị đã nhúng cứng vào bundle lúc build.
- Tạo user MySQL với `'app'@'localhost'` → pod ở node khác bị từ chối; file init ở đây dùng `'user'@'%'`.
- `order-service` trả 503 `UPSTREAM_ERROR` khi `product-service` chưa Ready — hành vi đúng; kiểm tra `kubectl get endpointslices`.



## 7. Reset dữ liệu

```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS shop_auth; DROP DATABASE IF EXISTS shop_catalog; DROP DATABASE IF EXISTS shop_orders;"
# sau đó chạy lại các file trong db/init
```

Trên K8s: xoá PVC để StatefulSet/Deployment tạo pod mới và init container chạy lại `db/init`.

## 8. Bài tập mở rộng

- Thêm batch endpoint `GET /api/v1/products/batch?ids=1,2,3` để `order-service` gọi một lần thay vì N lần.
- Cho `order-service` trừ tồn kho qua `POST /api/v1/products/{id}/reserve` (thử rồi sẽ thấy bài toán distributed transaction / saga).
- Tách `db/init/02-catalog-schema.sql` thành migration có version, chạy bằng init container.
- Thêm `metrics` endpoint (`/metrics` Prometheus) rồi cài kube-prometheus-stack.
- Cho mỗi service một `NetworkPolicy` mặc định deny-all, mở dần theo từng hướng (frontend → backend, order → product, backend → MySQL).

