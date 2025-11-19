from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter(tags=["root"])

INDEX_PATH = Path(__file__).resolve().parent.parent / "static" / "index.html"


def load_index_html() -> str:
    if INDEX_PATH.exists():
        return INDEX_PATH.read_text(encoding="utf-8")
    return "<html><body><h1>BreachScan Backend Running</h1><p>index.html not found.</p></body></html>"


@router.get("/", response_class=HTMLResponse)
def root():
    """Serve a simple landing page if `static/index.html` exists."""
    return load_index_html()
