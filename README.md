# Verbaflow

App de inglés por voz: grabar palabra o frase → STT (faster-whisper) → traducción Surplus → guardar y repasar (FSRS).

Proyecto independiente de podioTest.

## Estructura

| Carpeta | Rol |
|---------|-----|
| `api/` | FastAPI, PostgreSQL, Whisper, Surplus |
| `frontend/` | Angular (captura, biblioteca, repaso) |
| `api/k8s/` | Helm backend |
| `frontend/k8s/` | Helm frontend |

BD: base **`verbaflow`** en el mismo Postgres que `finance_portfolio` / `surplus_provider` (mismo usuario). El DDL lo aplicas tú en DBeaver; no va en git.

## Desarrollo local

```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8090

cd ../frontend
npm install && npm start
```

## Imágenes y CI

- `ghcr.io/juanfranvelilla/verbaflow-api`
- `ghcr.io/juanfranvelilla/verbaflow-frontend`

Jenkins (Kaniko): `api/Jenkinsfile` y `frontend/Jenkinsfile`. Detalle K8s: [k8s/README.md](k8s/README.md).

## Repo

https://github.com/juanFRANvelilla/verbaflow