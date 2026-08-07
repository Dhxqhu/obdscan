#!/usr/bin/env python3
"""Manufacturer pack registry."""

from __future__ import annotations

from .base import ManufacturerPack
from . import bmw, generic, mercedes, vag
from .others import EXTRA_PACKS

_PACKS: list[ManufacturerPack] = [
    generic.PACK,
    bmw.PACK,
    mercedes.PACK,
    vag.PACK,
    *EXTRA_PACKS,
]

# id -> pack
REGISTRY: dict[str, ManufacturerPack] = {p.id: p for p in _PACKS}


def list_packs() -> list[ManufacturerPack]:
    return list(_PACKS)


def get_pack(key: str) -> ManufacturerPack:
    key = key.strip().lower().replace(" ", "_").replace("-", "_")
    if key in REGISTRY:
        return REGISTRY[key]
    for p in _PACKS:
        aliases = {a.lower().replace(" ", "_").replace("-", "_") for a in p.aliases}
        aliases.add(p.name.lower().replace(" ", "_").replace("-", "_"))
        aliases.add(p.id)
        if key in aliases or any(key in a or a in key for a in aliases if len(key) >= 3):
            return p
    raise KeyError(
        f"Unknown manufacturer '{key}'. Try: {', '.join(sorted(REGISTRY))}"
    )


def search_packs(query: str) -> list[ManufacturerPack]:
    q = query.lower()
    hits = []
    for p in _PACKS:
        blob = " ".join([p.id, p.name, p.description, *p.aliases]).lower()
        if q in blob:
            hits.append(p)
    return hits
