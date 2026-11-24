# Verbaflow — Kubernetes

Un solo entorno (sin PRO ni Argo). Charts en `api/k8s` y `frontend/k8s`.

## Namespace

Todo en **`verbaflow`** (API y frontend; releases Helm `verbaflow-api` y `verbaflow-frontend`).

## URL pública

`https://verbaflow.juanfranciscoperez.es`

- `/` → frontend
- `/api`, `/health` → API

Gateway `lab`: listener `https-verbaflow` (certificado `verbaflow-gateway-tls` en `verbaflow-front`).

## Secrets

En **`verbaflow`**, secret `backend-secrets`:

- `DATABASE_URL` → BD `verbaflow` (o el nombre que uses en Postgres)
- `SURPLUSINTELLIGENCE_API_KEY`
- `SURPLUS_DATABASE_URL`
- Resto según `api/env.example`

En **`verbaflow`**: `ghcr-secret` para GHCR (copia desde otro namespace si hace falta).

## Despliegue (Helm directo)

```bash
helm upgrade --install verbaflow-api ./api/k8s \
  -n verbaflow \
  -f api/k8s/values.yaml \
  --set image.tag=2

helm upgrade --install verbaflow-frontend ./frontend/k8s \
  -n verbaflow \
  -f frontend/k8s/values.yaml \
  --set image.tag=2
```

Los Jenkins de Kaniko solo construyen y suben imagen; el deploy lo haces tú con estos comandos (o un job Jenkins aparte sin publicar a helm-charts/Argo).