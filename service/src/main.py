from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.decks import router as decks_router
from .settings import settings

logging.basicConfig(level=settings.log_level.upper())

app = FastAPI(
    title="DoDeck API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "prod" else None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/healthz")
def healthz():
    return {"ok": True, "version": app.version, "environment": settings.environment}


app.include_router(decks_router)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):  # pragma: no cover - last resort handler
    logging.exception("Unhandled error processing %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"error": "internal_error"})
