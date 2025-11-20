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
from datetime import datetime, timedelta


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
    Return cached assets; if cache is empty, lazily load from sample_assets.json.
    This ensures /tenable/assets has data even before an explicit refresh.
    """
    global _cached_assets
    if not _cached_assets:
        try:
            _cached_assets = _read_assets_from_file()
        except Exception:
            _cached_assets = []
    return _cached_assets


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


def _compute_next_run(schedule: dict) -> str | None:
    """Compute the next_run_at timestamp (ISO) for the given schedule.

    All times treated as naive UTC. If a once schedule is in the past,
    returns None. For recurring schedules, finds the next occurrence
    strictly after 'now'.
    """
    now = datetime.utcnow()
    t = schedule.get("time") or "00:00"
    try:
        hour, minute = [int(x) for x in t.split(":", 1)]
    except ValueError:
        hour, minute = 0, 0
    stype = schedule.get("type")
    if stype == "once":
        ds = schedule.get("date")
        if not ds:
            return None
        try:
            y, m, d = [int(x) for x in ds.split("-")]
            run_dt = datetime(y, m, d, hour, minute)
        except ValueError:
            return None
        if run_dt <= now:
            return None
        return run_dt.isoformat()
    if stype == "daily":
        run_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if run_dt <= now:
            run_dt += timedelta(days=1)
        return run_dt.isoformat()
    if stype == "weekly":
        day_name = schedule.get("day") or ""
        day_map = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}
        target_idx = day_map.get(day_name)
        if target_idx is None:
            return None
        current_idx = now.weekday()  # Monday=0
        days_ahead = (target_idx - current_idx) % 7
        run_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        if days_ahead == 0 and run_dt <= now:
            run_dt += timedelta(days=7)
        return run_dt.isoformat()
    # Fallback
    return None


def create_mock_scheduled_scan(name: str, targets: list[str], schedule: dict) -> dict:
    """Create a mock scheduled scan and store it in memory.

    Adds metadata fields:
    - created_at: ISO timestamp (UTC)
    - enabled: bool (always True initially)
    - expanded_target_count: number of discrete targets after expansion
    - next_run_at: first future run time (None if once schedule already past)
    """
    scan_id = str(uuid4())
    meta_schedule = dict(schedule)
    next_run = _compute_next_run(meta_schedule)
    scan = {
        "id": scan_id,
        "name": name,
        "targets": targets,
        "expanded_target_count": len(targets),
        "schedule": meta_schedule,
        "next_run_at": next_run,
        "created_at": datetime.utcnow().isoformat(),
        "enabled": True,
        "status": "scheduled",
    }
    _mock_scheduled_scans[scan_id] = scan
    return scan


def get_mock_scheduled_scan(scan_id: str) -> dict | None:
    return _mock_scheduled_scans.get(scan_id)


def list_mock_scheduled_scans() -> list[dict]:
    return list(_mock_scheduled_scans.values())


