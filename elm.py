#!/usr/bin/env python3
"""ELM327 session helpers for obdscan."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import serial


@dataclass
class ElmInfo:
    port: str
    version: str = "unknown"
    voltage: str | None = None
    protocol: str | None = None
    ecu_alive: bool = False


@dataclass
class ElmSession:
    port: str
    baud: int = 38400
    timeout: float = 2.0
    ser: serial.Serial | None = field(default=None, repr=False)
    info: ElmInfo | None = field(default=None, repr=False)

    @property
    def connected(self) -> bool:
        return bool(self.ser and self.ser.is_open)

    def open(self) -> ElmInfo:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        except serial.SerialException as exc:
            raise ConnectionError(f"Cannot open {self.port}: {exc}") from exc

        time.sleep(0.35)
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except OSError:
            pass

        reset = self.cmd("ATZ", wait=1.6)
        ver = self._extract_version(reset)
        if not ver:
            ati = self.cmd("ATI", wait=0.6)
            ver = self._extract_version(ati)
            if not ver:
                lines = [ln.strip() for ln in ati.splitlines() if ln.strip()]
                ver = lines[-1] if lines else "unknown"

        for setup in ("ATE0", "ATL0", "ATH0", "ATS0", "ATAT1"):
            self.cmd(setup, wait=0.3)

        voltage = None
        atrv = self.cmd("ATRV", wait=0.5)
        m = re.search(r"([\d.]+)\s*V", atrv, re.I)
        if m:
            voltage = f"{m.group(1)} V"

        self.cmd("ATSP0", wait=0.25)
        probe = self.cmd("0100", wait=2.0)
        up = probe.upper()
        ecu_alive = (
            bool(re.search(r"41\s*00", probe, re.I))
            and "NO DATA" not in up
            and "UNABLE" not in up
            and "ERROR" not in up
        )

        protocol = None
        atdp = self.cmd("ATDP", wait=0.4)
        lines = [
            ln.strip()
            for ln in atdp.splitlines()
            if ln.strip() and ln.strip().upper() not in {"OK", "ATDP", ">"}
        ]
        if lines:
            protocol = lines[-1]

        self.info = ElmInfo(self.port, ver or "unknown", voltage, protocol, ecu_alive)
        return self.info

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except OSError:
                pass
        self.ser = None

    def ensure(self) -> None:
        if not self.connected:
            raise ConnectionError("Not connected — open a session first")

    def cmd(self, command: str, wait: float = 0.5) -> str:
        self.ensure()
        assert self.ser is not None
        try:
            self.ser.reset_input_buffer()
            self.ser.write((command.strip() + "\r").encode())
        except OSError as exc:
            return f"ERROR: {exc}"
        time.sleep(wait)
        chunks: list[bytes] = []
        end = time.time() + max(self.timeout, wait)
        while time.time() < end:
            try:
                n = self.ser.in_waiting
            except OSError as exc:
                return f"ERROR: {exc}"
            if n:
                try:
                    chunks.append(self.ser.read(n))
                except OSError as exc:
                    return f"ERROR: {exc}"
                end = time.time() + 0.2
            else:
                time.sleep(0.04)
        return b"".join(chunks).decode(errors="replace").replace("\r", "\n")

    def reopen(self) -> ElmInfo:
        self.close()
        return self.open()

    @staticmethod
    def _extract_version(text: str) -> str | None:
        m = re.search(r"(ELM327[^\n>]*)", text, re.I)
        if m:
            return m.group(1).strip()
        for ln in text.splitlines():
            ln = ln.strip()
            if ln and ln.upper() not in {"ATZ", "ATI", "OK", ">"} and "SEARCHING" not in ln.upper():
                if re.search(r"ELM|\d+\.\d+", ln, re.I):
                    return ln
        return None


def decode_dtc_pair(a: int, b: int) -> str | None:
    if a == 0 and b == 0:
        return None
    system = "PCBU"[(a & 0xC0) >> 6]
    return f"{system}{(a & 0x30) >> 4:X}{a & 0x0F:X}{(b & 0xF0) >> 4:X}{b & 0x0F:X}"


def parse_dtc_response(text: str) -> list[str]:
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", text)
    codes: list[str] = []
    for hdr in ("43", "47", "4A"):
        idx = cleaned.upper().find(hdr)
        if idx < 0:
            continue
        payload = cleaned[idx + 2 :]
        for start in (0, 2):
            data = payload[start:]
            for i in range(0, len(data) - 3, 4):
                try:
                    a = int(data[i : i + 2], 16)
                    b = int(data[i + 2 : i + 4], 16)
                except ValueError:
                    break
                code = decode_dtc_pair(a, b)
                if code and code not in codes:
                    codes.append(code)
        if codes:
            break
    for m in re.finditer(r"\b([PCBU][0-9A-F]{4})\b", text.upper()):
        if m.group(1) not in codes and m.group(1) != "P0000":
            codes.append(m.group(1))
    return codes


def parse_mode01(text: str, pid: str) -> list[int] | None:
    hexes = [h.upper() for h in re.findall(r"[0-9A-Fa-f]{2}", text)]
    pid = pid.upper()
    for i in range(len(hexes) - 2):
        if hexes[i] == "41" and hexes[i + 1] == pid:
            return [int(h, 16) for h in hexes[i + 2 : i + 6]]
    return None
