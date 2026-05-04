"""Phase 5 — FastAPI backend: events, anomalies, stats, WebSocket."""

import logging
import os
from contextlib import asynccontextmanager

import motor.motor_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import anomalies, events, internal, stats, ws
from api.services.ws_manager import WebSocketManager

logger = logging.getLogger(__name__)

_DEFAULT_URL = "mongodb://pulse:pulse@localhost:27017/pulsecore?authSource=admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    url = os.getenv("MONGODB_URL", _DEFAULT_URL)
    client = motor.motor_asyncio.AsyncIOMotorClient(url)
    app.state.db = client["pulsecore"]
    app.state.mongo_client = client
    app.state.ws_manager = WebSocketManager()
    logger.info("MongoDB client created. URL=%s", url)
    try:
        yield
    finally:
        client.close()
        logger.info("MongoDB client closed.")


def create_app() -> FastAPI:
    app = FastAPI(title="PulseCore API", version="0.6.0", lifespan=lifespan)

    origins = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(events.router)
    app.include_router(anomalies.router)
    app.include_router(stats.router)
    app.include_router(ws.router)
    app.include_router(internal.router)

    @app.get("/health", tags=["ops"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
