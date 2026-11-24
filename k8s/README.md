# Verbaflow — Kubernetes

Mismo patrón que **surplus-satellite**: un solo entorno, `values-pre.yaml` para Jenkins (`DEPLOY_PRE`), namespace = nombre de la app.

## Namespace

**`verbaflow`** — API y frontend en el mismo namespace (releases `verbaflow-api` y `verbaflow-frontend`).

## URL pública

`https://verbaflow.juanfranciscoperez.es`

- `/` → frontend
- `/api`, `/health` → API

Gateway `lab`: listener **`https-verbaflow-pre`** (como `https-finance-pre`), TLS `verbaflow-gateway-tls` + `letsencrypt-ovh-prod`.

Tras el primer deploy del **frontend**, añade el listener al Gateway (una vez):

```bash
kubectl patch gateway lab -n jenkins --type=json \
  --patch-file k8s/bootstrap/gateway-lab-listener.json
```

En OVH/DNS: registro **A** (o el mismo patrón que `surplus-satellite.juanfranciscoperez.es`) para `verbaflow.juanfranciscoperez.es`.

## RBAC para Jenkins (obligatorio una vez)

Sin esto, `helm upgrade` falla con *cannot list resource "secrets" in namespace "verbaflow"*:

```bash
kubectl apply -f k8s/bootstrap/jenkins-rolebinding.yaml
kubectl apply -f k8s/bootstrap/jenkins-gateway-rbac.yaml
```

`edit` no basta: Helm necesita crear `HTTPRoute`, `Certificate`, etc. (`jenkins-gateway-rbac.yaml`).

## Secrets

En **`verbaflow`**:

- `backend-secrets` — `DATABASE_URL`, `SURPLUSINTELLIGENCE_API_KEY`, `SURPLUS_DATABASE_URL`, etc.
- `ghcr-secret` — pull de GHCR

## Despliegue

Jenkins (pipeline genérico) con `values-pre.yaml` y `image.tag=<BUILD_NUMBER>`.

Manual:

```bash
helm upgrade --install verbaflow-api ./api/k8s -n verbaflow \
  -f api/k8s/values-pre.yaml --set image.tag=2

helm upgrade --install verbaflow-frontend ./frontend/k8s -n verbaflow \
  -f frontend/k8s/values-pre.yaml --set image.tag=2
```