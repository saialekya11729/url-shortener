from fastapi import FastAPI

from app.database import Base, engine
from app.routers.pages import router as pages_router
from app.routers.urls import router as urls_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="Anonymous URL shortener with 24-hour link expiry.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(pages_router)
app.include_router(urls_router)

