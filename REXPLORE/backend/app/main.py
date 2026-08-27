"""
ReXplore backend entrypoint.

Local:
    uvicorn app.main:app --reload

Production:
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

import logging
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from app.config import get_settings
from app.database import init_db
from routers import auth, papers, queries, datasets, analytics
from services import embedding_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("rexplore")

settings = get_settings()

app = FastAPI(
    title="ReXplore API",
    description="Intelligent Semantic Research Understanding & Knowledge Discovery",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("ReXplore backend started. Database initialized.")

    # Warm the embedding model in the background instead of leaving it to
    # load lazily on the first paper's "Building Semantic Index" stage.
    # Importing sentence-transformers/torch and loading model weights is a
    # one-time cost (~10-30s) in a fresh process. On hosts that spin down
    # when idle (e.g. Render's free tier), every wake-up IS a fresh
    # process, so without this, whichever paper happens to be first after
    # each wake pays that cost on top of its own real encoding work - which
    # is what makes "Building Semantic Index" look consistently slow even
    # though the model only truly needs loading once per process.
    #
    # Runs on a background thread (not blocking startup/the health check)
    # so Render still sees the service come up promptly; the model is very
    # likely already warm by the time a user gets around to uploading.
    def _warm_up_embedding_model():
        try:
            embedding_service.warm_up()
            logger.info("Embedding model warmed up.")
        except Exception as exc:  # noqa: BLE001
            # Don't crash startup if the model can't load (e.g. no network
            # on first run) - papers fall back to keyword search exactly as
            # before via EmbeddingUnavailable.
            logger.warning("Could not warm up embedding model at startup: %s", exc)

    threading.Thread(target=_warm_up_embedding_model, daemon=True).start()


@app.get("/api/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "service": "ReXplore API",
    }


# API routers
app.include_router(auth.router)
app.include_router(papers.router)
app.include_router(queries.router)
app.include_router(datasets.router)
app.include_router(analytics.router)


# ---------------------------------------------------------
# React frontend
# ---------------------------------------------------------

# PROJECT-FILE-REXPLORE/
# ├── backend/
# │   └── app/main.py
# └── frontend/
#     └── dist/
#
# main.py -> app -> backend -> PROJECT-FILE-REXPLORE
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

logger.info("Frontend directory: %s", FRONTEND_DIST)


@app.get("/", include_in_schema=False)
async def frontend_root():
    index_file = FRONTEND_DIST / "index.html"

    if not index_file.exists():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend has not been built yet."
            },
        )

    return FileResponse(index_file)


# ---------------------------------------------------------
# SPA fallback for every other GET route
# ---------------------------------------------------------
#
# ReXplore's routes (/login, /upload, /papers/5, /profile, ...) only exist
# client-side, in React Router. Before this route, this backend had no
# catch-all: `StaticFiles(html=True)` mounted at "/" only serves *literal*
# files, so any direct navigation, browser refresh, bookmark, or hard
# redirect (e.g. api.js sending an expired session to /login via
# `window.location.href`) landed on a raw 404 JSON page with no way back
# into the app short of manually editing the URL back to "/".
#
# This route is registered last (after every /api/* router above), so
# FastAPI still matches real API paths first. For anything else it serves
# the actual built file when one exists (JS/CSS/images from `vite build`),
# and otherwise serves index.html so React Router can render the right
# screen for the requested URL - restoring normal SPA refresh/deep-link
# behavior without changing any API route, name, or response contract.
_FRONTEND_DIST_RESOLVED = FRONTEND_DIST.resolve()


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    # Never swallow a genuinely-missing API route into the SPA fallback -
    # keep returning a normal 404 for those, same as before.
    if full_path == "api" or full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    if full_path:
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_relative_to(_FRONTEND_DIST_RESOLVED) and candidate.is_file():
            return FileResponse(candidate)

    index_file = FRONTEND_DIST / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=503,
            content={"detail": "Frontend has not been built yet."},
        )
    return FileResponse(index_file)