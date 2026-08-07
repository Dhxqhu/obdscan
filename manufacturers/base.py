#!/usr/bin/env python3
"""Manufacturer pack base types + shared ISO UDS identifiers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class EcuModule:
    """One addressable ECU / diagnostic target."""

    address: int
    name: str
    description: str = ""
    # doip = ISO 13400 2-byte LA; hsfz = BMW 1-byte over :6801; either = try both maps
    addressing: str = "doip"  # doip | hsfz | either
    notes: str = ""

    @property
    def addr_hex(self) -> str:
        if self.address <= 0xFF:
            return f"0x{self.address:02X}"
        return f"0x{self.address:04X}"


@dataclass(frozen=True)
class DataIdentifier:
    did: int
    name: str
    description: str = ""

    @property
    def did_hex(self) -> str:
        return f"0x{self.did:04X}"


# ISO-ish / widely implemented DIDs (safe to probe on most UDS ECUs)
STANDARD_DIDS: tuple[DataIdentifier, ...] = (
    DataIdentifier(0xF190, "VIN", "Vehicle Identification Number"),
    DataIdentifier(0xF187, "spare_part_number", "Manufacturer spare part number"),
    DataIdentifier(0xF18A, "system_supplier_id", "System supplier identifier"),
    DataIdentifier(0xF18C, "ecu_serial", "ECU serial number"),
    DataIdentifier(0xF191, "hw_number", "Manufacturer ECU hardware number"),
    DataIdentifier(0xF192, "sw_number", "Manufacturer ECU software number"),
    DataIdentifier(0xF193, "hw_version", "Manufacturer ECU hardware version"),
    DataIdentifier(0xF195, "sw_version", "Manufacturer ECU software version"),
    DataIdentifier(0xF197, "system_name", "System name or engine type"),
    DataIdentifier(0xF198, "repair_shop_code", "Repair shop code / tester SN"),
    DataIdentifier(0xF199, "programming_date", "Programming date"),
    DataIdentifier(0xF19E, "as_amended", "ODX file identifier / ASAM"),
    DataIdentifier(0xF1A0, "boot_sw", "Boot software identification"),
    DataIdentifier(0xF1A1, "calib_id", "Calibration identification"),
    DataIdentifier(0xF1A2, "calib_ver", "Calibration verification number"),
    DataIdentifier(0xF1A8, "vehicle_mfg", "Vehicle manufacturer ECU software"),
    DataIdentifier(0xF1A9, "vehicle_mfg_ecu_sw", "Vehicle manufacturer ECU software number"),
    DataIdentifier(0xF1AA, "vehicle_mfg_ecu_hw", "Vehicle manufacturer ECU hardware number"),
)


@dataclass
class ManufacturerPack:
    """Selectable manufacturer library for enhanced diagnostics."""

    id: str
    name: str
    aliases: tuple[str, ...] = ()
    description: str = ""
    transports: tuple[str, ...] = ("doip",)  # doip, hsfz, isotp, elm
    default_doip_port: int = 13400
    default_hsfz_port: int = 6801
    tester_address: int = 0x0E80
    # Common gateway / functional addresses to try first
    gateway_addresses: tuple[int, ...] = ()
    modules: tuple[EcuModule, ...] = ()
    dids: tuple[DataIdentifier, ...] = field(default_factory=lambda: STANDARD_DIDS)
    # Typical link-local / OEM IP hints (not authoritative)
    ip_hints: tuple[str, ...] = ("169.254.1.20", "169.254.19.1", "192.168.0.10")
    sources: tuple[str, ...] = ()
    maturity: str = "scaffold"  # scaffold | community | experimental

    def all_addresses(self) -> list[int]:
        seen: set[int] = set()
        out: list[int] = []
        for a in list(self.gateway_addresses) + [m.address for m in self.modules]:
            if a not in seen:
                seen.add(a)
                out.append(a)
        return out

    def find_module(self, address: int) -> EcuModule | None:
        for m in self.modules:
            if m.address == address:
                return m
        return None

    def resolve_name(self, address: int) -> str:
        m = self.find_module(address)
        if m:
            return f"{m.name} ({m.addr_hex})"
        return f"ECU {address:#06x}" if address > 0xFF else f"ECU {address:#04x}"


def expand_bmw_hsfz_to_doip(modules: Iterable[EcuModule]) -> tuple[EcuModule, ...]:
    """BMW HSFZ uses 1-byte targets; some DoIP stacks map them as 0x10XX / 0x00XX."""
    out: list[EcuModule] = []
    seen: set[int] = set()
    for m in modules:
        for addr in (m.address, 0x1000 | m.address, m.address):
            if addr in seen:
                continue
            seen.add(addr)
            out.append(
                EcuModule(
                    address=addr,
                    name=m.name,
                    description=m.description,
                    addressing="either" if addr != m.address else m.addressing,
                    notes=m.notes
                    + ("" if addr == m.address else " (mapped from 1-byte HSFZ target)"),
                )
            )
    return tuple(out)
