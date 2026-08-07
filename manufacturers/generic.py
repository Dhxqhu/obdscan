#!/usr/bin/env python3
"""Generic DoIP / UDS pack — any modern DoIP vehicle."""

from __future__ import annotations

from .base import EcuModule, ManufacturerPack, STANDARD_DIDS

# Functional addressing / commonly seen gateway LAs across OEMs (public captures)
_MODULES = (
    EcuModule(0x0001, "FUNC", "Functional / broadcast diagnostic address", notes="may not answer"),
    EcuModule(0x00E0, "GATEWAY", "Generic gateway (example LA from doipclient docs)"),
    EcuModule(0x00E1, "GATEWAY_ALT", "Alternate gateway LA"),
    EcuModule(0x0E00, "TESTER_RANGE", "Tester address range marker (not an ECU)"),
    EcuModule(0x1010, "BMW_STYLE_GW", "Often seen BMW-style DoIP gateway LA"),
    EcuModule(0x4010, "VAG_STYLE_GW", "Seen in public Audi DoIP captures (0x4010)"),
    EcuModule(0x14DA, "MB_STYLE", "Example Mercedes-ish LA from public tooling notes"),
)

PACK = ManufacturerPack(
    id="generic",
    name="Generic DoIP / UDS",
    aliases=("iso", "doip", "uds", "any"),
    description=(
        "Manufacturer-agnostic DoIP client. Discovers vehicles via UDP announcement, "
        "activates routing, then lets you pick raw logical addresses. Use this when "
        "your OEM pack is incomplete — still needs a DoIP car + GT327 ethernet mode."
    ),
    transports=("doip",),
    gateway_addresses=(0x00E0, 0x1010, 0x4010),
    modules=_MODULES,
    dids=STANDARD_DIDS,
    ip_hints=("169.254.1.20", "169.254.19.1", "192.168.0.10", "192.168.8.1"),
    sources=(
        "ISO 13400 / ISO 14229",
        "https://github.com/jacobschaer/python-doipclient",
        "https://github.com/pylessard/python-udsoncan",
    ),
    maturity="community",
)
