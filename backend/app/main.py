"""FastAPI application for BBS Federal Spending Search."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load .env from project root (one level up from backend/)
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

from .routes import search, spending, reference, contract_detail, award_detail

app = FastAPI(title="BBS Spending Search", version="0.1.0")

_cors_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(spending.router)
app.include_router(reference.router)
app.include_router(contract_detail.router)
app.include_router(award_detail.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve React build in production (must be AFTER API routes)
_static_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _static_dir.is_dir():
    from starlette.responses import FileResponse

    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="static-assets")

    _static_root = _static_dir.resolve()

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = (_static_dir / full_path).resolve()
        if file_path.is_file() and str(file_path).startswith(str(_static_root)):
            return FileResponse(file_path)
        return FileResponse(_static_dir / "index.html")
