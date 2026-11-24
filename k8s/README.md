# Despliegue Kubernetes

Plantilla pendiente: `Deployment` + `Service` + `Ingress` TLS para `api` y `frontend`.

Variables sensibles via Secret: `DATABASE_URL`, `SURPLUSINTELLIGENCE_API_KEY`, `API_KEY`.

Considera un volumen o initContainer para cachear el modelo Whisper (`WHISPER_MODEL`).