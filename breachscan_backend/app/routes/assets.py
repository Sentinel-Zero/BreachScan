from fastapi import APIRouter, Path as ApiPath
from pathlib import Path
import json

router = APIRouter(prefix="/assets", tags=["assets"])

DATA_PATH = Path(__file__).resolve().parent.parent / "sample_assets.json"


def load_assets():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@router.get("")
def list_assets():
    """Return all assets with basic risk info."""
    return load_assets()


@router.get("/{asset_id}")
def get_asset(asset_id: str = ApiPath(..., example="host-1", description="ID of the asset to retrieve")):
    """Return a single asset by ID."""
    assets = load_assets()
    for asset in assets:
        if asset.get("id") == asset_id:
            return asset
    return {"error": "Asset not found"}
