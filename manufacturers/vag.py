#!/usr/bin/env python3
"""VAG (VW / Audi / Seat / Škoda / Bentley / Lamborghini) pack."""

from __future__ import annotations

from .base import DataIdentifier, EcuModule, ManufacturerPack, STANDARD_DIDS

# VAG historically used TP2.0 / UDS on CAN; newer MQB/MLB/PPE use DoIP.
# Addresses below are community scaffolds — logical addresses differ by platform.
_MODULES = (
    EcuModule(0x4010, "GATEWAY", "DoIP gateway (seen in public Audi captures)", "doip"),
    EcuModule(0x0010, "ENGINE", "Engine ECU (01)", "doip", notes="VAG label '01'"),
    EcuModule(0x0011, "ENGINE_SLAVE", "Engine slave / cylinder bank", "doip"),
    EcuModule(0x0002, "TRANS", "Transmission (02)", "doip"),
    EcuModule(0x0003, "ABS", "Brakes / ABS / ESC (03)", "doip"),
    EcuModule(0x0008, "HVAC", "HVAC (08)", "doip"),
    EcuModule(0x0009, "CENTRAL", "Central electronics / BCM (09)", "doip"),
    EcuModule(0x0013, "DISTRONIC", "ACC / Distonic", "doip"),
    EcuModule(0x0015, "AIRBAG", "Airbags (15)", "doip"),
    EcuModule(0x0016, "STEERING", "Steering wheel electronics", "doip"),
    EcuModule(0x0017, "CLUSTER", "Instrument cluster (17)", "doip"),
    EcuModule(0x0019, "CAN_GATEWAY", "CAN gateway (19)", "doip"),
    EcuModule(0x0025, "IMMO", "Immobilizer", "doip"),
    EcuModule(0x002B, "STEER_ASSIST", "Steering assist", "doip"),
    EcuModule(0x003C, "LANE", "Lane assist", "doip"),
    EcuModule(0x0042, "DOOR_DR", "Driver door", "doip"),
    EcuModule(0x0044, "STEERING_COL", "Steering column", "doip"),
    EcuModule(0x0046, "COMFORT", "Comfort system", "doip"),
    EcuModule(0x0052, "PASS_DOOR", "Passenger door", "doip"),
    EcuModule(0x005F, "INFORMATION", "Information electronics / MIB", "doip"),
    EcuModule(0x006C, "CAMERA", "Backup camera", "doip"),
    EcuModule(0x006D, "ASSIST", "Assistance systems", "doip"),
    EcuModule(0x0075, "TELEMATICS", "Telematics / OCU", "doip"),
    EcuModule(0x008C, "HYBRID", "Hybrid battery / BECM", "doip"),
    EcuModule(0x00A5, "FR_ASSIST", "Front assist / radar", "doip"),
    EcuModule(0x00BB, "BATT_MGMT", "Battery regulation", "doip"),
    EcuModule(0x00C6, "HEADLIGHT_L", "Headlight left", "doip"),
    EcuModule(0x00C7, "HEADLIGHT_R", "Headlight right", "doip"),
    # Classic KWP/TP2 module IDs sometimes still referenced in docs (CAN path)
    EcuModule(0x01, "TP2_ENGINE", "Legacy TP2.0 engine (needs CAN/TP2, not ELM)", "isotp"),
    EcuModule(0x02, "TP2_TRANS", "Legacy TP2.0 transmission", "isotp"),
    EcuModule(0x03, "TP2_ABS", "Legacy TP2.0 ABS", "isotp"),
    EcuModule(0x09, "TP2_CENTRAL", "Legacy TP2.0 central electrics", "isotp"),
    EcuModule(0x19, "TP2_GATEWAY", "Legacy TP2.0 gateway", "isotp"),
)

_VAG_DIDS = STANDARD_DIDS + (
    DataIdentifier(0xF19E, "odx_file", "ODX / ASAM file identifier"),
    DataIdentifier(0xF1A2, "cvn", "Calibration verification"),
    DataIdentifier(0x0405, "vag_adapt", "Adaptation channel style DID (varies wildly)"),
    DataIdentifier(0xF40C, "engine_speed", "Engine speed (UDS mapping varies)"),
)

PACK = ManufacturerPack(
    id="vag",
    name="VAG (VW / Audi / Seat / Škoda)",
    aliases=("vw", "audi", "seat", "skoda", "škoda", "bentley", "lambo", "lamborghini", "volkswagen", "cupra"),
    description=(
        "VAG enhanced diagnostics scaffold. Modern cars: DoIP. Older: TP2.0/UDS on CAN "
        "(needs SocketCAN interface — not the GT327 Bluetooth ELM path). No open ODIS "
        "replacement; this pack is address/DID scaffolding + discovery."
    ),
    transports=("doip", "isotp"),
    gateway_addresses=(0x4010, 0x0019),
    modules=_MODULES,
    dids=_VAG_DIDS,
    ip_hints=("169.254.1.20", "192.168.1.3", "192.168.0.10"),
    sources=(
        "Public DoIP capture examples (Audi 0x4010)",
        "https://github.com/rnd-ash/ecu_diagnostics (VW-TP2 transport)",
        "Community VAG UDS address lists",
    ),
    maturity="scaffold",
)
