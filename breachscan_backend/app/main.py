from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes.assets import router as assets_router
from app.routes.root import router as root_router
from app.routes.tenable import router as tenable_router


app = FastAPI(title="BreachScanner Backend")

# CORS so a frontend can talk to this later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can tighten this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(root_router)
app.include_router(assets_router)
app.include_router(tenable_router)

# Serve static assets (CSS/JS/pages) at /static
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
