from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import lookup, review, vocab
from app.settings import get_settings

app = FastAPI(title=get_settings().app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lookup.router)
app.include_router(vocab.router)
app.include_router(review.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().app_name}