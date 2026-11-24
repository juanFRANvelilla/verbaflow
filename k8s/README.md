# Verbaflow — Kubernetes

Un solo entorno (sin PRO ni Argo). Charts en `api/k8s` y `frontend/k8s`.

## Namespaces

| Componente | Namespace |
|------------|-----------|
| API | `verbaflow-back` |
| Frontend | `verbaflow-front` |

## URL pública

`https://verbaflow.juanfranciscoperez.es`

- `/` → frontend
- `/api`, `/health` → API

Gateway `lab`: listener `https-verbaflow` (certificado `verbaflow-gateway-tls` en `verbaflow-front`).

## Secrets

En **`verbaflow-back`**, secret `backend-secrets`:

- `DATABASE_URL` → BD `verbaflow` (o el nombre que uses en Postgres)
- `SURPLUSINTELLIGENCE_API_KEY`
- `SURPLUS_DATABASE_URL`
- Resto según `api/env.example`

En **`verbaflow-back`** y **`verbaflow-front`**: `ghcr-secret` para GHCR.

## Despliegue (Helm directo)

```bash
helm upgrade --install back ./api/k8s \
  -n verbaflow-back --create-namespace \
  -f api/k8s/values.yaml \
  --set image.tag=v123

helm upgrade --install front ./frontend/k8s \
  -n verbaflow-front --create-namespace \
  -f frontend/k8s/values.yaml \
  --set image.tag=v123
```

Los Jenkins de Kaniko solo construyen y suben imagen; el deploy lo haces tú con estos comandos (o un job Jenkins aparte sin publicar a helm-charts/Argo).