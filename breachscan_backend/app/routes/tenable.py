"""Mock Tenable integration routes.

These endpoints call functions in `tenable_client` which currently read
local `sample_assets.json` data to simulate Tenable.io/Nessus responses.
In a future iteration, the tenable_client module will be replaced (or
extended) to perform real API calls via `pyTenable`, handle pagination,
normalize fields, and apply any enrichment logic.

Important: Do not treat this data as authoritative; it's purely lab/mock.
"""

# app/routes/tenable.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from datetime import date as Date
import ipaddress
from ..tenable_client import (
    refresh_assets_from_tenable,
    get_cached_assets,
    get_cached_asset_by_id,
    peek_assets_from_tenable,
    create_mock_scheduled_scan,
    get_mock_scheduled_scan,
    list_mock_scheduled_scans,
)

class RefreshRequest(BaseModel):
    limit: int | None = Field(None, ge=1, description="Optionally limit number of assets to load")
    dry_run: bool = Field(False, description="If true, do not cache; just preview the load")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"dry_run": True, "limit": 2},
                {"limit": 1},
                {}
            ]
        }
    }


router = APIRouter(prefix="/tenable", tags=["tenable"])


@router.post("/refresh")
def refresh_tenable_assets(body: RefreshRequest | None = None):
    """
    Mock 'refresh from Tenable' – loads assets from sample_assets.json.
    Accepts optional parameters to preview (dry run) or limit the load.
    """
    opts = body or RefreshRequest()
    if opts.dry_run:
        assets = peek_assets_from_tenable(limit=opts.limit)
        return {"status": "dry_run", "asset_count": len(assets)}
    assets = refresh_assets_from_tenable(limit=opts.limit)
    return {"status": "ok", "asset_count": len(assets)}


# -----------------------------
# Scheduled Scans (mock)
# -----------------------------
class ScheduleModel(BaseModel):
    type: Literal["once", "daily", "weekly"] = "once"
    day: str | None = Field(None, description="Required if type=weekly, e.g., 'Sunday'")
    date: Date | None = Field(None, description="Required if type=once; YYYY-MM-DD")
    time: str = Field(
        ..., 
        description="HH:MM in 24h format, e.g., 02:00",
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        examples=["02:00", "14:30"],
    )

    @model_validator(mode="after")
    def _check_day_vs_type(self):
        if self.type == "weekly":
            if not self.day:
                raise ValueError("'day' is required when type=weekly")
            # 'date' not used for weekly
            self.date = None
        else:
            # Not weekly: ignore day
            self.day = None

        if self.type == "once":
            if self.date is None:
                raise ValueError("'date' is required when type=once")
        else:
            # Not once: ignore date
            self.date = None
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"type": "once", "date": "2025-11-20", "time": "02:00"},
                {"type": "daily", "time": "03:30"},
                {"type": "weekly", "day": "Sunday", "time": "01:15"}
            ]
        }
    }


class CreateScheduledScanRequest(BaseModel):
    name: str
    targets: list[str] = Field(
        ...,
        description=(
            "IPv4 targets as a list of tokens. Each token may be: "
            "a single IP (10.0.0.10), a CIDR (10.0.0.0/30), or a dash range "
            "(10.0.0.10-10.0.0.20). Tokens expand to individual IPs server-side."
        ),
    )
    schedule: ScheduleModel

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Weekly External",
                    "targets": ["10.0.0.10", "10.0.0.11"],
                    "schedule": {"type": "weekly", "day": "Sunday", "time": "02:00"}
                },
                {
                    "name": "One-off Patch Window",
                    "targets": ["10.0.0.0/30"],
                    "schedule": {"type": "once", "date": "2025-11-25", "time": "23:00"}
                }
            ]
        }
    }


@router.post("/scheduled-scans")
def create_scheduled_scan(body: CreateScheduledScanRequest):
    expanded = _expand_targets(body.targets)
    sch = body.schedule.model_dump()
    # Normalize date to ISO string for predictable JSON to the UI
    if isinstance(sch.get("date"), Date):
        sch["date"] = sch["date"].isoformat()
    scan = create_mock_scheduled_scan(
        name=body.name,
        targets=expanded,
        schedule=sch,
    )
    return scan


@router.get("/scheduled-scans")
def list_scheduled_scans():
    return {"scans": list_mock_scheduled_scans()}


@router.get("/scheduled-scans/{scan_id}")
def get_scheduled_scan(scan_id: str):
    scan = get_mock_scheduled_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scheduled scan not found")
    return scan


# -----------------------------
# Helpers
# -----------------------------
MAX_TARGETS_EXPANSION = 4096


def _expand_targets(tokens: list[str]) -> list[str]:
    """Expand a list of target tokens into discrete IPv4 addresses.

    Supports:
    - Single IPv4: "10.0.0.10"
    - CIDR: "10.0.0.0/30" (hosts only)
    - Dash range: "10.0.0.10-10.0.0.20"
    """
    out: list[str] = []
    for raw in tokens:
        t = (raw or "").strip()
        if not t:
            continue

        # CIDR
        try:
            net = ipaddress.ip_network(t, strict=False)
            if isinstance(net, ipaddress.IPv4Network):
                for ip in net.hosts():
                    out.append(str(ip))
                    if len(out) > MAX_TARGETS_EXPANSION:
                        raise HTTPException(status_code=400, detail="Target expansion exceeds limit")
                continue
        except ValueError:
            pass

        # Dash range
        if "-" in t:
            a, b = t.split("-", 1)
            try:
                ipa = ipaddress.ip_address(a.strip())
                ipb = ipaddress.ip_address(b.strip())
                if ipa.version == 4 and ipb.version == 4:
                    start = int(ipa)
                    end = int(ipb)
                    if end < start:
                        start, end = end, start
                    for i in range(start, end + 1):
                        out.append(str(ipaddress.IPv4Address(i)))
                        if len(out) > MAX_TARGETS_EXPANSION:
                            raise HTTPException(status_code=400, detail="Target expansion exceeds limit")
                    continue
            except ValueError:
                pass

        # Single IP
        try:
            ip = ipaddress.ip_address(t)
            if ip.version == 4:
                out.append(str(ip))
                continue
        except ValueError:
            pass

        raise HTTPException(status_code=400, detail=f"Invalid target token: {t}")

    if not out:
        raise HTTPException(status_code=400, detail="No valid targets parsed")
    return out


@router.get("/assets")
def list_tenable_assets():
    """
    Return the cached Tenable-style assets.
    """
    assets = get_cached_assets()
    return {"assets": assets}


@router.get("/assets/{asset_id}")
def get_tenable_asset(asset_id: str):
    """
    Return a single cached asset.
    """
    asset = get_cached_asset_by_id(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


