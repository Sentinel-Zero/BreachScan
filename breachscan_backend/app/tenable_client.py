"""
Mock Tenable client for development/testing.

This module imitates fetching asset data from Tenable.io/Nessus. 
It DOES NOT perform any external API calls. Instead, it reads from `sample_assets.json` to
simulate responses you might receive from Tenable. As the project evolves,
these functions can be replaced with real calls via `pyTenable` and proper
normalization.

Important:
- Do not put real credentials in code; use environment variables/.env.
- See `app/config.py` for settings wiring.
"""

# app/tenable_client.py
from pathlib import Path
import json
from typing import List, Dict, Any
from uuid import uuid4


DATA_PATH = Path(__file__).resolve().parent / "sample_assets.json"

# Simple in-memory cache for mock assets
_cached_assets: List[Dict[str, Any]] | None = None

 
def _read_assets_from_file() -> List[Dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def refresh_assets_from_tenable(limit: int | None = None) -> List[Dict[str, Any]]:
    """
    Mock 'refresh from Tenable' by loading asset data from sample_assets.json,
    optionally limiting the number of cached assets.

    Later this function will call the real Tenable API (via pyTenable)
    and normalize the results into the same structure.
    """
    global _cached_assets
    data = _read_assets_from_file()
    if isinstance(limit, int) and limit > 0:
        data = data[:limit]
    _cached_assets = data
    return _cached_assets


def get_cached_assets() -> List[Dict[str, Any]]:
    """
    Return the cached assets if we've 'refreshed' them,
    otherwise return an empty list.
    """
    return _cached_assets or []


def get_cached_asset_by_id(asset_id: str) -> Dict[str, Any] | None:
    """
    Return a single asset from the cache by its id.
    """
    assets = get_cached_assets()
    for asset in assets:
        if asset.get("id") == asset_id:
            return asset
    return None

def peek_assets_from_tenable(limit: int | None = None) -> List[Dict[str, Any]]:
    """Load assets without updating the cache (useful for dry runs)."""
    data = _read_assets_from_file()
    if isinstance(limit, int) and limit > 0:
        data = data[:limit]
    return data


# -----------------------------
# Mock scheduled scans (in-memory)
# -----------------------------
_mock_scheduled_scans: dict[str, dict] = {}


def create_mock_scheduled_scan(name: str, targets: list[str], schedule: dict) -> dict:
    """Create a mock scheduled scan and store it in memory."""
    scan_id = str(uuid4())
    scan = {
        "id": scan_id,
        "name": name,
        "targets": targets,
        "schedule": schedule,
        "status": "scheduled",
    }
    _mock_scheduled_scans[scan_id] = scan
    return scan


def get_mock_scheduled_scan(scan_id: str) -> dict | None:
    return _mock_scheduled_scans.get(scan_id)


def list_mock_scheduled_scans() -> list[dict]:
    return list(_mock_scheduled_scans.values())


