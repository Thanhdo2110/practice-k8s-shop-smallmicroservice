# Infra manifests — shop-k8s lab (kubeadm)

Các manifest trong thư mục này là phần hạ tầng đã cấu hình cho cụm lab
(`control-plane 192.168.0.110`, `worker-node01/02/03`, K8s `v1.28.15`).
Chúng **không** thay thế manifest upstream; chỉ là các patch/CR cần thiết để
tái tạo đúng trạng thái đang chạy.

## Phiên bản đang dùng

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Kubernetes | `v1.28.15` | kubeadm, 1 control-plane + 3 worker |
| Calico | `v3.26.1` | pod CIDR mới `10.244.0.0/16` |
| ingress-nginx | `v1.12.8` | 2 replica, `ETP: Local` |
| MetalLB | `v0.14.9` | L2 mode, pool `192.168.0.120-125` |
| cert-manager | `v1.16.5` | self-signed issuer |
| App | 4 deployment × 3 replica | `maxSurge: 1`, `maxUnavailable: 0` |

## Thứ tự áp dụng

### 1. Calico — đổi pod CIDR

```bash
kubectl apply -f k8s-manifests/infra/calico/ippool-pods-10-244.yaml
kubectl apply -f k8s-manifests/infra/calico/ippool-default-disabled.yaml

# Bat buoc: kube-proxy phai biet pod CIDR moi, neu khong NodePort se hong
# (traffic LAN bi coi la pod traffic -> DNAT cheo node -> treo).
kubectl -n kube-system get cm kube-proxy -o json \
  | jq -r '.data["config.conf"]' \
  | sed 's#clusterCIDR: 192.168.0.0/16#clusterCIDR: 10.244.0.0/16#' > /tmp/kube-proxy.conf
kubectl -n kube-system patch cm kube-proxy --type=merge \
  -p "$(jq -n --arg cfg "$(cat /tmp/kube-proxy.conf)" '{data:{"config.conf":$cfg}}')"
kubectl -n kube-system rollout restart ds/kube-proxy
kubectl -n kube-system rollout status ds/kube-proxy --timeout=300s
```

Sau đó rolling restart workload để pod mới nhận IP `10.244.x`:

```bash
for d in auth-service product-service order-service frontendthk8s; do
  kubectl -n shop-k8s rollout restart deploy/$d
  kubectl -n shop-k8s rollout status deploy/$d --timeout=600s
done
```

> **Quan trọng:** 4 deployment app dùng `topologySpreadConstraints` với
> `maxSkew: 1`, `DoNotSchedule`. Phải có `nodeTaintsPolicy: Honor` (đã có
> trong `base/*/deployment.yaml`), nếu không control-plane bị taint sẽ được
> tính là domain 0 pod và pod surge thứ 4 không thể schedule.

### 2. ingress-nginx

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.8/deploy/static/provider/baremetal/deploy.yaml

# Tat metrics (lab yeu, khong can Prometheus)
kubectl -n ingress-nginx patch deploy ingress-nginx-controller --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--enable-metrics=false"}]'

# Hien ADDRESS cua Ingress = VIP (lay tu Service)
kubectl -n ingress-nginx patch deploy ingress-nginx-controller --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--publish-service=$(POD_NAMESPACE)/ingress-nginx-controller"}]'

# HA: 2 replica, spread DoNotSchedule, maxUnavailable 0
kubectl -n ingress-nginx patch deploy ingress-nginx-controller \
  --patch-file k8s-manifests/infra/ingress-nginx/controller-ha-patch.yaml.patch
kubectl apply -f k8s-manifests/infra/ingress-nginx/pdb.yaml
```

### 3. MetalLB

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml
kubectl -n metallb-system rollout status deploy/controller --timeout=300s
kubectl apply -f k8s-manifests/infra/metallb/ipaddresspool.yaml
kubectl apply -f k8s-manifests/infra/metallb/l2advertisement.yaml
```

Sau đó chuyển Service ingress-nginx sang LoadBalancer:

```bash
kubectl apply -f k8s-manifests/infra/ingress-nginx/service.yaml
kubectl -n ingress-nginx get svc ingress-nginx-controller
# EXTERNAL-IP phai la 192.168.0.120
```

### 4. cert-manager + TLS self-signed

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.5/cert-manager.yaml
kubectl -n cert-manager rollout status deploy/cert-manager --timeout=300s
kubectl -n cert-manager rollout status deploy/cert-manager-webhook --timeout=300s
kubectl -n cert-manager rollout status deploy/cert-manager-cainjector --timeout=300s

kubectl apply -f k8s-manifests/infra/cert-manager/clusterissuer-selfsigned.yaml
kubectl apply -f k8s-manifests/base/ingress/ingress-tls.yaml
kubectl -n shop-k8s wait --for=condition=Ready certificate/shop-k8s-tls --timeout=180s
```

Client test thêm vào `/etc/hosts`:

```
192.168.0.120  shop.example.com
```

> `hsts: "false"` đang bật trong Ingress TLS vì cert self-signed. Khi có cert
> thật (Cloudflare/Let's Encrypt) thì bỏ annotation này và bật lại HSTS.

## Kiểm tra nhanh

```bash
# VIP + API
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.0.120/
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.0.120/api/v1/products

# TLS (bo qua verify vi self-signed)
curl -sk -o /dev/null -w '%{http_code}\n' \
  --resolve shop.example.com:443:192.168.0.120 https://shop.example.com/
curl -sk -o /dev/null -w '%{http_code}\n' \
  --resolve shop.example.com:443:192.168.0.120 https://shop.example.com/api/v1/products

# HTTP -> HTTPS
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' \
  -H 'Host: shop.example.com' http://192.168.0.120/

# Trang thai
kubectl -n ingress-nginx get deploy,pods,pdb,svc
kubectl -n metallb-system get ipaddresspool,l2advertisement
kubectl -n shop-k8s get deploy,pods,ingress,certificate
```

## Hành vi cần biết

- **`ETP: Local`:** NodePort chỉ phục vụ trên node đang có pod ingress
  (`worker-node02`, `worker-node03`). `worker-node01:32277` sẽ fail — đúng
  thiết kế, không phải lỗi. Dùng VIP `192.168.0.120` làm endpoint chính.
- **MetalLB L2:** khi ingress rollout, VIP chuyển node announce → vài giây
  gián đoạn. Muốn zero-downtime tuyệt đối phải dùng `ETP: Cluster` (mất
  client IP) hoặc BGP/ECMP.
- **Cert self-signed:** browser cảnh báo; bấm Advanced → Proceed. Cert tự
  renew trước `notAfter` 30 ngày (renewalTime ~12/01/2027).
- **Control-plane yếu:** 2 vCPU / 2.5 GB RAM. Cài cert-manager từng làm API
  server chậm >5s khiến scheduler/controller-manager mất leader election và
  restart. Tránh cài thêm thành phần nặng cùng lúc.

## Rollback

### App deployment

```bash
kubectl -n shop-k8s rollout undo deploy/auth-service
kubectl -n shop-k8s rollout undo deploy/product-service
kubectl -n shop-k8s rollout undo deploy/order-service
kubectl -n shop-k8s rollout undo deploy/frontendthk8s
```

Lưu ý: `rollout undo` chỉ đổi image/template, không đưa pod về IP cũ; pod vẫn
nhận IP từ pool đang active.

### TLS

```bash
kubectl -n shop-k8s delete ingress shop-k8s-ingress-tls
kubectl -n shop-k8s delete certificate shop-k8s-tls
kubectl -n shop-k8s delete secret shop-k8s-tls
kubectl delete clusterissuer selfsigned
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.5/cert-manager.yaml
```

### MetalLB / VIP

```bash
# Quay Service ve NodePort, bo annotation VIP
kubectl -n ingress-nginx patch svc ingress-nginx-controller --type=json -p '[
  {"op":"remove","path":"/metadata/annotations/metallb.io~1loadBalancerIPs"},
  {"op":"replace","path":"/spec/type","value":"NodePort"},
  {"op":"remove","path":"/spec/externalTrafficPolicy"}
]'
kubectl delete -f k8s-manifests/infra/metallb/l2advertisement.yaml
kubectl delete -f k8s-manifests/infra/metallb/ipaddresspool.yaml
kubectl delete -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml
```

### ingress-nginx HA

```bash
kubectl -n ingress-nginx scale deploy/ingress-nginx-controller --replicas=1
kubectl -n ingress-nginx delete pdb ingress-nginx-controller
# Bo spread constraint:
kubectl -n ingress-nginx patch deploy ingress-nginx-controller --type=json \
  -p '[{"op":"remove","path":"/spec/template/spec/topologySpreadConstraints"}]'
# Bo --publish-service neu muon ADDRESS trong (check index truoc bang
#   kubectl -n ingress-nginx get deploy ingress-nginx-controller \
#     -o jsonpath='{range .spec.template.spec.containers[0].args[*]}{.}{"\n"}{end}'
# thuong la index 9 neu da them --enable-metrics=false):
kubectl -n ingress-nginx patch deploy ingress-nginx-controller --type=json \
  -p '[{"op":"remove","path":"/spec/template/spec/containers/0/args/9"}]'
```

### Calico (chi lam khi that su can quay lai pool cu)

1. Bat lai pool cu, tat pool moi.
2. Đảm bảo không còn pod nào dùng IP `10.244.x` (rolling restart toàn bộ
   workload và đợi pod cũ biến mất).
3. Xoá pool `pods-10-244` và đổi `clusterCIDR` kube-proxy về
   `192.168.0.0/16`, restart DaemonSet.

Không xoá pool khi còn pod đang giữ IP từ pool đó.

## Backup trước khi thay đổi

Bản backup manifest gốc ngày `2026-11-12` nằm tại
`/home/dont/backup/shop-k8s-2026-11-12/` (quyền `700`).
