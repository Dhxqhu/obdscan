#!/usr/bin/env python3
"""BMW manufacturer pack — community ECU tables (HSFZ + DoIP hints)."""

from __future__ import annotations

from .base import DataIdentifier, EcuModule, ManufacturerPack, STANDARD_DIDS, expand_bmw_hsfz_to_doip

# One-byte diagnostic targets used on K+DCAN / HSFZ (beemuu community table)
_HSFZ = (
    EcuModule(0x12, "DME", "Engine control (Digital Motor Electronics)", "hsfz"),
    EcuModule(0x18, "EGS", "Transmission control", "hsfz"),
    EcuModule(0x29, "DSC", "Dynamic stability control (ABS/DSC)", "hsfz"),
    EcuModule(0x19, "DSC_ALT", "DSC chassis variant (5-Series/X5 style)", "hsfz"),
    EcuModule(0x40, "CAS", "Car access system (immobiliser, keys)", "hsfz"),
    EcuModule(0x60, "KOMBI", "Instrument cluster", "hsfz"),
    EcuModule(0x0D, "KOMBI_ALT", "Instrument cluster secondary target", "hsfz"),
    EcuModule(0x72, "FRM", "Footwell module (lighting)", "hsfz"),
    EcuModule(0x78, "IHKA", "Climate control", "hsfz"),
    EcuModule(0x01, "ACSM", "Crash safety / airbags", "hsfz"),
    EcuModule(0x30, "EPS", "Electric power steering", "hsfz"),
    EcuModule(0x64, "PDC", "Park distance control", "hsfz"),
    EcuModule(0x65, "SZL", "Steering column switch cluster", "hsfz"),
    EcuModule(0x70, "RAD", "Radio / head unit", "hsfz"),
    EcuModule(0x56, "BODY", "Body-domain (doors/locks) F-series role", "hsfz"),
    EcuModule(0x63, "GWS", "Gear selector / transmission variant", "hsfz"),
    EcuModule(0x07, "SME", "HV battery management (PHEV/BEV)", "hsfz"),
    EcuModule(0x10, "ZGW", "Central gateway (typical HSFZ target)", "hsfz"),
    EcuModule(0x13, "DDE", "Diesel engine electronics", "hsfz"),
    EcuModule(0x21, "EKP", "Fuel pump control", "hsfz"),
    EcuModule(0x2E, "RSE", "Rear seat entertainment", "hsfz"),
    EcuModule(0x36, "HUD", "Head-up display", "hsfz"),
    EcuModule(0x39, "VGSG", "Transfer case / xDrive", "hsfz"),
    EcuModule(0x41, "ZGM", "Central gateway module alias", "hsfz"),
    EcuModule(0x44, "TBX", "Telematics / Combox", "hsfz"),
    EcuModule(0x5E, "JBE", "Junction box electronics", "hsfz"),
    EcuModule(0x61, "MASK", "Navigation / CCC / CHAMP family", "hsfz"),
    EcuModule(0x73, "AHM", "Trailer module", "hsfz"),
    EcuModule(0x76, "CVM", "Convertible top module", "hsfz"),
    EcuModule(0x7F, "NVE", "Night vision", "hsfz"),
)

# Explicit DoIP 2-byte LAs reported in public captures / tooling
_DOIP_EXTRA = (
    EcuModule(0x1010, "DOIP_GW", "BMW-style DoIP gateway logical address", "doip"),
    EcuModule(0x1000, "DOIP_BASE", "DoIP base / functional-ish", "doip"),
)

_BMW_DIDS = STANDARD_DIDS + (
    DataIdentifier(0x1000, "bmw_ident_block", "Often used identity/read block (vehicle-specific)"),
    DataIdentifier(0xF150, "bmw_hw_ref", "Community-probed hardware reference DID"),
    DataIdentifier(0xF151, "bmw_sw_ref", "Community-probed software reference DID"),
    DataIdentifier(0xDBE4, "wheel_speeds", "Wheel-speed related (OBDb/community)"),
    DataIdentifier(0xD240, "vehicle_speed", "Vehicle speed DID (community)"),
    DataIdentifier(0xD107, "kombi_speed_alt", "Cluster speed alternate"),
    DataIdentifier(0xD031, "current_gear", "Current gear (community)"),
    DataIdentifier(0xDCDD, "body_states", "Door/hood/trunk/lock states (community)"),
)

PACK = ManufacturerPack(
    id="bmw",
    name="BMW / MINI",
    aliases=("mini", "rolls", "rr", "beemuu", "bmw_m", "motorrad"),
    description=(
        "BMW/MINI enhanced diagnostics. GT327 ethernet DoIP switch is for ISO DoIP cars; "
        "many F/G cars also speak BMW HSFZ on TCP 6801 (1-byte addresses). This pack lists "
        "community HSFZ targets and common DoIP LAs. Full coding still needs EDIABAS/ISTA data."
    ),
    transports=("doip", "hsfz"),
    default_doip_port=13400,
    default_hsfz_port=6801,
    tester_address=0x0E80,
    gateway_addresses=(0x1010, 0x10, 0x41),
    modules=expand_bmw_hsfz_to_doip(_HSFZ) + _DOIP_EXTRA,
    dids=_BMW_DIDS,
    ip_hints=("169.254.1.20", "169.254.19.1", "192.168.0.1"),
    sources=(
        "https://github.com/ohgeeceee/beemuu (ECU table)",
        "https://github.com/uholeschak/ediabaslib",
        "https://github.com/emdzej/ediabasx",
        "https://munich.dissec.to/kb/chapters/doip/doip.html",
    ),
    maturity="community",
)
