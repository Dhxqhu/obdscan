#!/usr/bin/env python3
"""Mercedes-Benz / Daimler manufacturer pack."""

from __future__ import annotations

from .base import DataIdentifier, EcuModule, ManufacturerPack, STANDARD_DIDS

# Public / community DoIP & UDS logical addresses (scaffold — vary by chassis)
_MODULES = (
    EcuModule(0x0001, "CGW", "Central gateway", "doip"),
    EcuModule(0x0010, "ME", "Engine control (ME / MED / CR)", "doip"),
    EcuModule(0x0011, "CDI", "Diesel CDI engine", "doip"),
    EcuModule(0x0012, "ISMSM", "Starter / ISM related", "doip"),
    EcuModule(0x0014, "EGS", "Transmission (EGS / VGS)", "doip"),
    EcuModule(0x0015, "VG", "Transfer case", "doip"),
    EcuModule(0x0020, "ESP", "ESP / ABS", "doip"),
    EcuModule(0x0021, "EHB", "SBC / brake hydraulics", "doip"),
    EcuModule(0x0023, "EPB", "Electric parking brake", "doip"),
    EcuModule(0x0030, "AIRBAG", "SRS / ORC", "doip"),
    EcuModule(0x0040, "IC", "Instrument cluster", "doip"),
    EcuModule(0x0044, "SAM_F", "Signal acquisition front", "doip"),
    EcuModule(0x0045, "SAM_R", "Signal acquisition rear", "doip"),
    EcuModule(0x0050, "HVAC", "Climate control", "doip"),
    EcuModule(0x0060, "DOOR_FL", "Door control front left", "doip"),
    EcuModule(0x0061, "DOOR_FR", "Door control front right", "doip"),
    EcuModule(0x0062, "DOOR_RL", "Door control rear left", "doip"),
    EcuModule(0x0063, "DOOR_RR", "Door control rear right", "doip"),
    EcuModule(0x0070, "HU", "Head unit / COMAND / MBUX", "doip"),
    EcuModule(0x0074, "TELE", "Telematics / HERMES", "doip"),
    EcuModule(0x0080, "TPMS", "Tire pressure", "doip"),
    EcuModule(0x0090, "PARK", "Park assist / PTS", "doip"),
    EcuModule(0x00A0, "SCM", "Steering column module", "doip"),
    EcuModule(0x00B0, "RFK", "Rear camera", "doip"),
    EcuModule(0x00C0, "BMS", "HV battery (EQ / hybrid)", "doip"),
    EcuModule(0x00D0, "CPC", "Powertrain control / CPC", "doip"),
    EcuModule(0x14DA, "DOIP_ENT", "DoIP entity example LA from tooling notes", "doip"),
    EcuModule(0x1D0C, "ZUS_GW", "Additional gateway-style LA (scaffold)", "doip"),
)

_MB_DIDS = STANDARD_DIDS + (
    DataIdentifier(0xF100, "mb_active_diag", "Active diagnostic information (varies)"),
    DataIdentifier(0xF111, "mb_variant", "Variant coding block (vehicle-specific)"),
    DataIdentifier(0xF121, "mb_status", "Status bitfield (vehicle-specific)"),
)

PACK = ManufacturerPack(
    id="mercedes",
    name="Mercedes-Benz / Daimler",
    aliases=("mb", "benz", "daimler", "smart", "mercedes_benz", "amg", "sprinter"),
    description=(
        "Mercedes DoIP/UDS scaffold. Newer models expose DoIP on OBD ethernet; "
        "rich procedure packs live in proprietary CBF/Xentry data. OpenVehicleDiag "
        "can convert CBF→JSON if you legally have those files."
    ),
    transports=("doip", "isotp"),
    gateway_addresses=(0x0001, 0x14DA),
    modules=_MODULES,
    dids=_MB_DIDS,
    ip_hints=("169.254.1.20", "172.29.1.1", "192.168.0.10"),
    sources=(
        "https://github.com/rnd-ash/OpenVehicleDiag",
        "https://github.com/rnd-ash/openStar",
        "ISO 13400 public captures",
    ),
    maturity="scaffold",
)
