# Verbaflow

App de inglés por voz: grabar palabra o frase → STT (faster-whisper) → traducción Surplus → guardar y repasar (FSRS).

Proyecto independiente de podioTest.

## Estructura

| Carpeta | Rol |
|---------|-----|
| `api/` | FastAPI, PostgreSQL, Whisper, Surplus |
| `frontend/` | Angular (captura, biblioteca, repaso) |
| `api/sql/` | SQL de creación de BD (homelab compartido) |
| `k8s/` | Despliegue en el clúster |

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

## Repo

https://github.com/juanFRANvelilla/verbaflow