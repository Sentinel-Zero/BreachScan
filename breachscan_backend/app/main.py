from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

app = FastAPI(title="BreachScanner Backend")

# CORS so a frontend can talk to this later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # you can tighten this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "sample_assets.json"


def load_assets():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/assets")
def list_assets():
    """
    Return all assets with basic risk info.
    """
    return load_assets()


@app.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    """
    Return a single asset by ID.
    """
    assets = load_assets()
    for asset in assets:
        if asset["id"] == asset_id:
            return asset
    return {"error": "Asset not found"}
