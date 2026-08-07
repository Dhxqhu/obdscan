#!/usr/bin/env python3
"""Generic SAE/ISO DTC lookup table helpers."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DTC_DB = HERE / "data" / "dtc_generic.json"


def load_dtc_db(path: Path | None = None) -> dict[str, str]:
    path = path or DEFAULT_DTC_DB
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return {str(k).upper(): str(v) for k, v in data.items()}
    out: dict[str, str] = {}
    for row in data:
        code = str(row.get("Code") or row.get("code") or "").split("/")[0].upper()
        desc = str(row.get("Description") or row.get("description") or "")
        if code:
            out[code] = desc
    return out


def lookup_code(db: dict[str, str], code: str) -> str:
    code = code.strip().upper()
    if code in db:
        return db[code]
    if len(code) == 5 and code[0] in "PBCU":
        family = {"P": "Powertrain", "B": "Body", "C": "Chassis", "U": "Network"}[code[0]]
        if code[1] in "13":
            return f"{family} — manufacturer-specific (not in generic SAE table)"
        return f"{family} — unknown generic code"
    return "Unrecognized code format"
