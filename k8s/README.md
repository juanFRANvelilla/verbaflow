# Verbaflow — Kubernetes

Charts Helm en `api/k8s` (backend) y `frontend/k8s`, mismo patrón que `finance_portfolio`.

## Hosts (Gateway)

| Entorno | Host |
|---------|------|
| PRE | `https://pre.verbaflow.juanfranciscoperez.es` |
| PRO | `https://pro.verbaflow.juanfranciscoperez.es` |

Rutas:

- `/` → frontend (`front`)
- `/api` y `/health` → API (`back`)

## Secrets (por namespace)

En `pre-verbaflow-back` y `pro-verbaflow-back`, crea `backend-secrets` con al menos:

- `DATABASE_URL` — `postgresql+asyncpg://…/verbaflow_pre` o `verbaflow_pro`
- `SURPLUSINTELLIGENCE_API_KEY`
- `SURPLUS_DATABASE_URL` (satélite / favoritos)
- Opcional: `API_KEY`, claves Whisper/Surplus según `api/env.example`

En cada namespace del backend, `ghcr-secret` para tirar imágenes de GHCR.

## Despliegue manual

```bash
# API PRE
helm upgrade --install back ./api/k8s \
  -n pre-verbaflow-back --create-namespace \
  -f api/k8s/values-pre.yaml \
  --set image.tag=v123

# Front PRE
helm upgrade --install front ./frontend/k8s \
  -n pre-verbaflow-front --create-namespace \
  -f frontend/k8s/values-pre.yaml \
  --set image.tag=v123
```

Añade en el Gateway `lab` los listeners `https-verbaflow-pre` y `https-verbaflow-pro` (como `https-finance-pre`).