#!/usr/bin/env python3
"""
DoIP + UDS session helpers for obdscan enhanced diagnostics.

Uses python-doipclient + python-udsoncan when installed. Works with the
GODIAG GT327 ethernet/DoIP path on compatible vehicles.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass, field
from typing import Any

from manufacturers.base import DataIdentifier, ManufacturerPack

try:
    from doipclient import DoIPClient
    from doipclient.connectors import DoIPClientUDSConnector
    from udsoncan.client import Client
    from udsoncan.exceptions import NegativeResponseException, TimeoutException
    from udsoncan.services import DiagnosticSessionControl

    HAS_DOIP = True
except ImportError:  # pragma: no cover
    HAS_DOIP = False
    DoIPClient = None  # type: ignore
    Client = None  # type: ignore


@dataclass
class DiscoveredVehicle:
    ip: str
    logical_address: int
    vin: str = ""
    eid: bytes = b""
    gid: bytes = b""
    raw: Any = None


@dataclass
class DoipSession:
    pack: ManufacturerPack
    ip: str
    logical_address: int
    client_logical_address: int = 0x0E80
    tcp_port: int = 13400
    _doip: Any = field(default=None, repr=False)
    _client: Any = field(default=None, repr=False)

    def connect(self) -> None:
        if not HAS_DOIP:
            raise RuntimeError(
                "DoIP stack not installed. Run: pip install doipclient udsoncan"
            )
        self._doip = DoIPClient(
            self.ip,
            self.logical_address,
            client_logical_address=self.client_logical_address,
            tcp_port=self.tcp_port,
        )
        conn = DoIPClientUDSConnector(self._doip)
        self._client = Client(conn, request_timeout=3)

    def close(self) -> None:
        try:
            if self._client:
                self._client.close()
        except Exception:
            pass
        try:
            if self._doip:
                self._doip.close()
        except Exception:
            pass
        self._client = None
        self._doip = None

    def __enter__(self) -> "DoipSession":
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def client(self):
        if not self._client:
            raise RuntimeError("DoIP session not connected")
        return self._client

    def change_session(self, session: int = 3) -> str:
        # 1=default, 2=programming, 3=extended
        try:
            self.client.change_session(session)
            return f"session {session} OK"
        except NegativeResponseException as exc:
            return f"NRC: {exc.response.code_name}"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def tester_present(self) -> str:
        try:
            self.client.tester_present()
            return "OK"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def read_did(self, did: int) -> tuple[bool, bytes | str]:
        try:
            resp = self.client.read_data_by_identifier(did)
            data = resp.service_data.values.get(did, b"")
            return True, data
        except NegativeResponseException as exc:
            return False, f"NRC {exc.response.code_name}"
        except TimeoutException:
            return False, "timeout"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def read_dtcs(self) -> tuple[bool, list[str] | str]:
        """UDS 0x19 read DTCs — best-effort decode to P0xxx-ish strings when possible."""
        try:
            # reportType 0x02 = reportDTCByStatusMask, mask 0xFF
            resp = self.client.get_dtc_by_status_mask(0xFF)
            dtcs = []
            for item in getattr(resp.service_data, "dtcs", []) or []:
                dtcs.append(str(item))
            return True, dtcs
        except NegativeResponseException as exc:
            return False, f"NRC {exc.response.code_name}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def clear_dtcs(self) -> tuple[bool, str]:
        try:
            self.client.clear_dtc()
            return True, "cleared"
        except NegativeResponseException as exc:
            return False, f"NRC {exc.response.code_name}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)


def discover_vehicles(timeout: float = 5.0) -> list[DiscoveredVehicle]:
    """UDP vehicle identification (DoIP)."""
    if not HAS_DOIP:
        raise RuntimeError("doipclient not installed")

    found: list[DiscoveredVehicle] = []

    # Primary: library helper (single best response)
    try:
        ann = DoIPClient.get_entity(ecu_ip_address="255.255.255.255")
        if ann is not None:
            ip = getattr(ann, "ip_address", None) or getattr(ann, "ecu_ip_address", None)
            # Some versions attach IP separately — also try str fields
            if ip is None:
                ip = getattr(ann, "ip", None)
            la = getattr(ann, "logical_address", None)
            vin = getattr(ann, "vin", "") or ""
            if la is not None:
                found.append(
                    DiscoveredVehicle(
                        ip=str(ip or "0.0.0.0"),
                        logical_address=int(la),
                        vin=str(vin).strip("\x00"),
                        raw=ann,
                    )
                )
    except Exception:
        pass

    # Also listen for power-on announcements briefly
    try:
        ann = DoIPClient.await_vehicle_announcement(timeout=min(timeout, 3.0))
        if ann is not None:
            # returns (address, announcement) in some versions
            if isinstance(ann, tuple) and len(ann) >= 2:
                addr, msg = ann[0], ann[1]
                ip = addr[0] if isinstance(addr, tuple) else str(addr)
                la = getattr(msg, "logical_address", 0)
                vin = getattr(msg, "vin", "") or ""
                found.append(
                    DiscoveredVehicle(ip=str(ip), logical_address=int(la), vin=str(vin).strip("\x00"), raw=ann)
                )
    except Exception:
        pass

    # Raw UDP fallback / multi-response collector
    found.extend(_raw_udp_discover(timeout=timeout))
    return _unique(found)


def _raw_udp_discover(timeout: float = 5.0) -> list[DiscoveredVehicle]:
    """Minimal ISO 13400 vehicle identification request."""
    # Protocol version 0x02, inverse 0xFD, payload type 0x0001, length 0
    packet = bytes([0x02, 0xFD, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    results: list[DiscoveredVehicle] = []
    try:
        sock.bind(("", 13400))
        sock.sendto(packet, ("255.255.255.255", 13400))
        end = timeout
        import time

        deadline = time.time() + end
        while time.time() < deadline:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                break
            if len(data) < 41:
                continue
            # parse announcement: after 8-byte header → VIN(17) + LA(2) + EID(6) + GID(6)...
            payload = data[8:]
            vin = payload[0:17].decode(errors="replace").strip("\x00")
            la = struct.unpack(">H", payload[17:19])[0]
            results.append(
                DiscoveredVehicle(ip=addr[0], logical_address=la, vin=vin, raw=data)
            )
    finally:
        sock.close()
    return results


def _unique(items: list[DiscoveredVehicle]) -> list[DiscoveredVehicle]:
    seen: set[tuple[str, int]] = set()
    out: list[DiscoveredVehicle] = []
    for v in items:
        key = (v.ip, v.logical_address)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def format_did_value(data: bytes | str) -> str:
    if isinstance(data, str):
        return data
    try:
        text = data.decode("ascii")
        if text.isprintable():
            return text
    except Exception:
        pass
    return data.hex(" ")


def probe_pack_modules(
    pack: ManufacturerPack,
    ip: str,
    addresses: list[int] | None = None,
    timeout_each: float = 1.5,
) -> list[tuple[int, str, str]]:
    """
    Try tester-present / default session on each LA.
    Returns list of (address, name, status).
    """
    if not HAS_DOIP:
        raise RuntimeError("doipclient/udsoncan not installed")

    addrs = addresses or pack.all_addresses()
    results: list[tuple[int, str, str]] = []
    for la in addrs:
        name = pack.resolve_name(la)
        try:
            with DoipSession(
                pack=pack,
                ip=ip,
                logical_address=la,
                client_logical_address=pack.tester_address,
                tcp_port=pack.default_doip_port,
            ) as sess:
                # shorten timeout
                sess.client.config["request_timeout"] = timeout_each
                msg = sess.change_session(DiagnosticSessionControl.Session.defaultSession)
                if "OK" in msg:
                    results.append((la, name, "alive"))
                else:
                    results.append((la, name, msg))
        except Exception as exc:  # noqa: BLE001
            results.append((la, name, f"fail: {exc}"))
    return results


def read_interesting_dids(
    session: DoipSession, dids: tuple[DataIdentifier, ...]
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for d in dids:
        ok, val = session.read_did(d.did)
        rows.append((f"{d.did_hex} {d.name}", format_did_value(val) if ok else str(val)))
    return rows
