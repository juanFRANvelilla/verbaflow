from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import SessionLocal
from app.routers import languages, lookup, vocab
from app.services.users import seed_bootstrap
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as db:
        await seed_bootstrap(db)
    yield


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lookup.router)
app.include_router(vocab.router)
app.include_router(languages.router)


@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().app_name}