#!/usr/bin/env python3
"""
obdscan — full-featured CLI OBD-II application for ELM327 dongles.

Interactive module menu (default) or scriptable subcommands.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("Missing dependency: rich  (pip install rich)", file=sys.stderr)
    sys.exit(1)

from dtc_db import DEFAULT_DTC_DB, load_dtc_db, lookup_code
from elm import ElmSession, parse_dtc_response, parse_mode01

try:
    from enhanced import interactive_enhanced_menu, show_manufacturer_list, show_pack_detail
    from manufacturers import get_pack, list_packs
    from doip_session import HAS_DOIP, discover_vehicles, probe_pack_modules, DoipSession, read_interesting_dids
except ImportError as _enh_exc:  # pragma: no cover
    interactive_enhanced_menu = None  # type: ignore
    HAS_DOIP = False
    _IMPORT_ERR = _enh_exc
else:
    _IMPORT_ERR = None

CONSOLE = Console()
HERE = Path(__file__).resolve().parent
DEFAULT_PORT = os.environ.get("OBD_PORT", "/dev/rfcomm0")
SAVED_CODES_DIR = Path.home() / "Documents" / "Saved Codes"

# PID catalog: name -> (mode01 hex, unit label, formatter(data_bytes)->str)
PID_CATALOG: dict[str, tuple[str, str, object]] = {
    "RPM": ("0C", "rpm", lambda d: f"{((d[0] << 8) + d[1]) / 4:.0f}" if len(d) >= 2 else "—"),
    "SPEED": ("0D", "km/h", lambda d: f"{d[0]}" if d else "—"),
    "COOLANT": ("05", "°C", lambda d: f"{d[0] - 40}" if d else "—"),
    "LOAD": ("04", "%", lambda d: f"{d[0] * 100 / 255:.1f}" if d else "—"),
    "THROTTLE": ("11", "%", lambda d: f"{d[0] * 100 / 255:.1f}" if d else "—"),
    "IAT": ("0F", "°C", lambda d: f"{d[0] - 40}" if d else "—"),
    "MAF": ("10", "g/s", lambda d: f"{((d[0] << 8) + d[1]) / 100:.2f}" if len(d) >= 2 else "—"),
    "MAP": ("0B", "kPa", lambda d: f"{d[0]}" if d else "—"),
    "FUEL_LEVEL": ("2F", "%", lambda d: f"{d[0] * 100 / 255:.1f}" if d else "—"),
    "TIMING": ("0E", "°", lambda d: f"{d[0] / 2 - 64:.1f}" if d else "—"),
    "STFT_B1": ("06", "%", lambda d: f"{(d[0] - 128) * 100 / 128:.1f}" if d else "—"),
    "LTFT_B1": ("07", "%", lambda d: f"{(d[0] - 128) * 100 / 128:.1f}" if d else "—"),
    "O2_B1S1": ("14", "V", lambda d: f"{d[0] / 200:.3f}" if d else "—"),
    "RUNTIME": ("1F", "s", lambda d: f"{(d[0] << 8) + d[1]}" if len(d) >= 2 else "—"),
    "MIL_DIST": ("21", "km", lambda d: f"{(d[0] << 8) + d[1]}" if len(d) >= 2 else "—"),
    "FUEL_RATE": ("5E", "L/h", lambda d: f"{((d[0] << 8) + d[1]) / 20:.2f}" if len(d) >= 2 else "—"),
    "BARO": ("33", "kPa", lambda d: f"{d[0]}" if d else "—"),
    "CTRL_MOD_V": ("42", "V", lambda d: f"{((d[0] << 8) + d[1]) / 1000:.3f}" if len(d) >= 2 else "—"),
    "ABS_LOAD": ("43", "%", lambda d: f"{((d[0] << 8) + d[1]) * 100 / 255:.1f}" if len(d) >= 2 else "—"),
    "AMBIENT": ("46", "°C", lambda d: f"{d[0] - 40}" if d else "—"),
    "ETHANOL": ("52", "%", lambda d: f"{d[0] * 100 / 255:.1f}" if d else "—"),
    "OIL_TEMP": ("5C", "°C", lambda d: f"{d[0] - 40}" if d else "—"),
}

DEFAULT_LIVE = ["RPM", "SPEED", "COOLANT", "LOAD", "THROTTLE"]

# Common raw commands shown by `help` in the raw AT/OBD prompt
RAW_AT_COMMANDS: list[tuple[str, str]] = [
    ("ATZ", "Reset adapter"),
    ("ATI", "Adapter identification"),
    ("ATRV", "Adapter-measured battery voltage"),
    ("ATDP", "Describe current protocol"),
    ("ATDPN", "Protocol number"),
    ("ATSP0", "Auto protocol select"),
    ("ATE0", "Echo off"),
    ("ATE1", "Echo on"),
    ("ATH0", "Headers off"),
    ("ATH1", "Headers on"),
    ("ATL0", "Linefeeds off"),
    ("ATWS", "Warm start"),
]

RAW_OBD_COMMANDS: list[tuple[str, str]] = [
    ("03", "Read stored DTCs"),
    ("04", "Clear DTCs / MIL"),
    ("07", "Read pending DTCs"),
    ("0A", "Read permanent DTCs"),
    ("0100", "Supported Mode 01 PIDs 01–20"),
    ("0101", "Monitor status / MIL"),
    ("0902", "VIN"),
]


class App:
    """Interactive OBD CLI application."""

    def __init__(self, port: str, baud: int, timeout: float, dtc_db: Path):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.db = load_dtc_db(dtc_db)
        self.session = ElmSession(port, baud, timeout)
        self.live_pids = list(DEFAULT_LIVE)

    # --- connection ---------------------------------------------------------

    def connect(self, quiet: bool = False) -> bool:
        try:
            info = self.session.open()
        except ConnectionError as exc:
            CONSOLE.print(f"[red]{exc}[/]")
            CONSOLE.print("[dim]./obdscan/connect-bt.sh[/]")
            return False
        if not quiet:
            self.show_status()
            if not info.ecu_alive:
                CONSOLE.print(
                    "[yellow]No ECU yet[/] — normal on a bench supply. "
                    "DTCs/live data need a vehicle."
                )
        return True

    def disconnect(self) -> None:
        self.session.close()
        CONSOLE.print("[dim]Disconnected.[/]")

    def require_session(self) -> bool:
        if self.session.connected:
            return True
        CONSOLE.print("[cyan]Not connected — opening adapter…[/]")
        return self.connect()

    def show_status(self) -> None:
        info = self.session.info
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("Port", self.port)
        if info:
            table.add_row("ELM", info.version)
            table.add_row("Voltage", info.voltage or "—")
            table.add_row("Protocol", info.protocol or "—")
            table.add_row(
                "ECU",
                "[green]responding[/]" if info.ecu_alive else "[yellow]no response[/]",
            )
        else:
            table.add_row("Session", "[red]closed[/]")
        table.add_row("DTC table", f"{len(self.db)} generic codes")
        CONSOLE.print(Panel(table, title="Connection", border_style="cyan"))

    # --- modules ------------------------------------------------------------

    def module_read_codes(self, force: bool = False) -> None:
        rows = self._fetch_dtc_rows(force=force)
        if rows is None:
            return
        self._render_codes(rows)
        if sys.stdin.isatty() and Confirm.ask(
            "Save codes + vehicle info to Documents/Saved Codes?", default=False
        ):
            path = self._save_codes_report(rows)
            if path:
                CONSOLE.print(f"[green]Saved[/] → {path}")

    def module_save_codes(self, force: bool = False) -> None:
        """Read DTCs and vehicle info, then write a text report under Documents/Saved Codes."""
        rows = self._fetch_dtc_rows(force=force)
        if rows is None:
            return
        self._render_codes(rows)
        path = self._save_codes_report(rows)
        if path:
            CONSOLE.print(f"[green]Saved[/] → {path}")

    def module_clear_codes(self, yes: bool = False) -> None:
        if not self.require_session():
            return
        if not yes:
            if not sys.stdin.isatty():
                CONSOLE.print("[yellow]Refusing clear without --yes in non-interactive mode.[/]")
                return
            if not Confirm.ask(
                "[yellow]Clear stored DTCs and freeze-frame data?[/]", default=False
            ):
                CONSOLE.print("[dim]Cancelled.[/]")
                return
        resp = self.session.cmd("04", wait=2.0)
        cleaned = re.sub(r"\s", "", resp.upper())
        if "OK" in resp.upper() or "44" in cleaned:
            CONSOLE.print("[green]Clear command accepted.[/] Re-read codes to verify.")
        else:
            CONSOLE.print(Panel(resp or "(empty)", title="Response", border_style="yellow"))

    def module_live_data(self, once: bool = False, interval: float = 0.4) -> None:
        if not self.require_session():
            return
        pids = self.live_pids
        CONSOLE.print(
            f"[dim]PIDs: {', '.join(pids)}  ·  configure in menu option 5  ·  Ctrl+C to stop[/]\n"
        )
        try:
            if once:
                CONSOLE.print(self._live_table(pids))
                return
            with Live(self._live_table(pids), console=CONSOLE, refresh_per_second=4) as live:
                while True:
                    live.update(self._live_table(pids))
                    time.sleep(interval)
        except KeyboardInterrupt:
            CONSOLE.print("\n[dim]Live data stopped.[/]")

    def module_configure_live(self) -> None:
        CONSOLE.print(Panel(
            "Enter PID names separated by spaces.\n"
            f"Available: {', '.join(sorted(PID_CATALOG))}",
            title="Live data PIDs",
            border_style="blue",
        ))
        raw = Prompt.ask("PIDs", default=" ".join(self.live_pids))
        chosen = []
        for name in raw.replace(",", " ").split():
            key = name.strip().upper()
            if key in PID_CATALOG:
                chosen.append(key)
            else:
                CONSOLE.print(f"[yellow]Skip unknown:[/] {name}")
        if chosen:
            self.live_pids = chosen
            CONSOLE.print(f"[green]Set:[/] {', '.join(self.live_pids)}")

    def module_vehicle_info(self) -> None:
        if not self.require_session():
            return
        info = self._collect_vehicle_info()
        table = Table(title="Vehicle / ECU info")
        table.add_column("Item", style="cyan")
        table.add_column("Value")
        for label, value in info.items():
            table.add_row(label, value)
        CONSOLE.print(table)

    def module_readiness(self) -> None:
        if not self.require_session():
            return
        resp = self.session.cmd("0101", wait=1.5)
        data = parse_mode01(resp, "01")
        if not data or len(data) < 4:
            CONSOLE.print("[yellow]No readiness data (need ECU).[/]")
            CONSOLE.print(Panel(resp, title="Raw", border_style="dim"))
            return
        a, b, c, d = data[0], data[1], data[2], data[3]
        mil_on = bool(a & 0x80)
        dtc_count = a & 0x7F
        table = Table(title="Monitor readiness (Mode 01 PID 01)")
        table.add_column("Monitor")
        table.add_column("Status")
        table.add_row("MIL", "[red]ON[/]" if mil_on else "[green]OFF[/]")
        table.add_row("DTC count", str(dtc_count))

        for name, available, incomplete in (
            ("Misfire", bool(b & 0x01), bool(b & 0x10)),
            ("Fuel system", bool(b & 0x02), bool(b & 0x20)),
            ("Components", bool(b & 0x04), bool(b & 0x40)),
        ):
            if not available:
                status = "[dim]n/a[/]"
            elif incomplete:
                status = "[yellow]incomplete[/]"
            else:
                status = "[green]ready[/]"
            table.add_row(name, status)

        spark = not bool(b & 0x08)
        for name, bit in (
            ("Catalyst", 0x01),
            ("Heated catalyst", 0x02),
            ("Evaporative system", 0x04),
            ("Secondary air", 0x08),
            ("A/C refrigerant", 0x10),
            ("Oxygen sensor", 0x20),
            ("Oxygen sensor heater", 0x40),
            ("EGR system", 0x80),
        ):
            supported = bool(c & bit)
            incomplete = bool(d & bit)
            if not supported:
                status = "[dim]n/a[/]"
            elif incomplete:
                status = "[yellow]incomplete[/]"
            else:
                status = "[green]ready[/]"
            table.add_row(name, status)

        CONSOLE.print(table)
        CONSOLE.print(f"[dim]Ignition type: {'spark' if spark else 'compression'}[/]")

    def module_freeze_frame(self) -> None:
        if not self.require_session():
            return
        # Mode 02 PID 02 = DTC that caused freeze frame; then sample common PIDs
        resp = self.session.cmd("0202", wait=1.5)
        CONSOLE.print(Panel(resp.strip() or "(empty)", title="Freeze frame DTC (02 02)", border_style="blue"))
        table = Table(title="Freeze frame sample (frame 00)")
        table.add_column("PID")
        table.add_column("Value")
        for name in ("RPM", "SPEED", "COOLANT", "LOAD", "THROTTLE"):
            pid = PID_CATALOG[name][0]
            raw = self.session.cmd(f"02{pid}00", wait=1.0)
            # Mode 02 responses start with 42
            hexes = [h.upper() for h in re.findall(r"[0-9A-Fa-f]{2}", raw)]
            val = "—"
            for i in range(len(hexes) - 3):
                if hexes[i] == "42" and hexes[i + 1] == pid.upper():
                    # skip frame byte sometimes
                    data = [int(h, 16) for h in hexes[i + 2 : i + 6]]
                    # if first data looks like frame 00, shift
                    if data and data[0] == 0 and len(hexes) > i + 3:
                        data = [int(h, 16) for h in hexes[i + 3 : i + 7]]
                    val = PID_CATALOG[name][2](data)
                    break
            table.add_row(name, val)
        CONSOLE.print(table)

    def module_lookup(self, codes: list[str] | None = None) -> None:
        if not codes:
            raw = Prompt.ask("Enter code(s)", default="P0420")
            codes = raw.replace(",", " ").split()
        table = Table(title="DTC lookup")
        table.add_column("Code", style="bold yellow")
        table.add_column("Description")
        for code in codes:
            table.add_row(code.strip().upper(), lookup_code(self.db, code))
        CONSOLE.print(table)

    def _show_raw_help(self) -> None:
        at = Table(title="AT commands (adapter)")
        at.add_column("Command", style="cyan")
        at.add_column("Description")
        for cmd, desc in RAW_AT_COMMANDS:
            at.add_row(cmd, desc)

        obd = Table(title="OBD commands (vehicle)")
        obd.add_column("Command", style="cyan")
        obd.add_column("Description")
        for cmd, desc in RAW_OBD_COMMANDS:
            obd.add_row(cmd, desc)
        for name, (pid, unit, _) in sorted(PID_CATALOG.items()):
            obd.add_row(f"01{pid}", f"{name} ({unit})")

        CONSOLE.print(at)
        CONSOLE.print(obd)
        CONSOLE.print("[dim]Type any of the above, or another AT/OBD hex string, then Enter.[/]")

    def module_raw(self, command: str | None = None) -> None:
        if command and command.strip().lower() == "help":
            self._show_raw_help()
            return
        if not self.require_session():
            return
        while True:
            if not command:
                command = Prompt.ask(
                    "AT / OBD command (type help for command list)",
                    default="010C",
                )
            if command.strip().lower() == "help":
                self._show_raw_help()
                command = None
                continue
            break
        resp = self.session.cmd(command, wait=1.5)
        CONSOLE.print(Panel(resp.strip() or "(empty)", title=f"Raw · {command}", border_style="magenta"))

    def module_pid_list(self) -> None:
        table = Table(title="Built-in live PIDs")
        table.add_column("Name", style="cyan")
        table.add_column("Mode 01")
        table.add_column("Unit")
        for name, (pid, unit, _) in sorted(PID_CATALOG.items()):
            mark = "★" if name in self.live_pids else ""
            table.add_row(f"{mark}{name}", f"01{pid}", unit)
        CONSOLE.print(table)
        CONSOLE.print("[dim]★ = currently selected for live data[/]")

    def module_enhanced(self) -> None:
        if interactive_enhanced_menu is None:
            CONSOLE.print(f"[red]Enhanced module failed to import:[/] {_IMPORT_ERR}")
            return
        interactive_enhanced_menu()

    def module_list_manufacturers(self) -> None:
        if interactive_enhanced_menu is None:
            CONSOLE.print(f"[red]Manufacturers failed to import:[/] {_IMPORT_ERR}")
            return
        show_manufacturer_list()

    # --- helpers ------------------------------------------------------------

    def _fetch_dtc_rows(self, force: bool = False) -> list[tuple[str, str]] | None:
        """Read stored/pending/permanent DTCs. Returns None if aborted."""
        if not self.require_session():
            return None
        info = self.session.info
        if info and not info.ecu_alive and not force:
            if sys.stdin.isatty():
                if not Confirm.ask("No ECU detected. Query DTCs anyway?", default=False):
                    return None
            else:
                CONSOLE.print(
                    "[yellow]No ECU detected.[/] Re-run with [bold]--force[/] to query anyway."
                )
                return None
        CONSOLE.print("[cyan]Reading DTCs[/] (stored / pending / permanent)…")
        rows: list[tuple[str, str]] = []
        for label, cmd in (("Stored", "03"), ("Pending", "07"), ("Permanent", "0A")):
            resp = self.session.cmd(cmd, wait=2.0)
            if any(x in resp.upper() for x in ("NO DATA", "UNABLE", "ERROR")):
                continue
            for code in parse_dtc_response(resp):
                rows.append((label, code))
        return rows

    def _collect_vehicle_info(self) -> dict[str, str]:
        """Gather VIN, MIL, a few PIDs, and adapter identity for display / save."""
        out: dict[str, str] = {}
        vin = self._read_vin()
        out["VIN"] = vin or "—"
        mil = self._read_mil()
        out["MIL"] = mil or "—"
        for label, pid, unit, fmt in (
            ("Battery (PID 42)", "42", "V", PID_CATALOG["CTRL_MOD_V"][2]),
            ("Fuel level", "2F", "%", PID_CATALOG["FUEL_LEVEL"][2]),
            ("Runtime", "1F", "s", PID_CATALOG["RUNTIME"][2]),
        ):
            val = self._query_pid(pid, fmt)
            out[label] = f"{val} {unit}" if val != "—" else "—"
        for atcmd, label in (("ATI", "Adapter"), ("ATRV", "Voltage"), ("ATDP", "Protocol")):
            resp = self.session.cmd(atcmd, wait=0.5)
            line = next(
                (
                    ln.strip()
                    for ln in resp.splitlines()
                    if ln.strip() and ln.strip().upper() not in {atcmd, "OK", ">"}
                ),
                "—",
            )
            out[label] = line
        sess = self.session.info
        if sess:
            out["ELM"] = sess.version or "—"
            if sess.voltage and out.get("Voltage") in (None, "—"):
                out["Voltage"] = sess.voltage
            if sess.protocol and out.get("Protocol") in (None, "—"):
                out["Protocol"] = sess.protocol
        out["Port"] = self.port
        return out

    def _save_codes_report(self, rows: list[tuple[str, str]]) -> Path | None:
        """Write DTC + vehicle info text file under Documents/Saved Codes."""
        CONSOLE.print("[cyan]Collecting vehicle info…[/]")
        vehicle = self._collect_vehicle_info()
        SAVED_CODES_DIR.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        vin = vehicle.get("VIN", "—")
        vin_part = ""
        if vin and vin != "—" and re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin.upper()):
            vin_part = f"_{vin.upper()}"
        path = SAVED_CODES_DIR / f"dtc_{stamp}{vin_part}.txt"

        lines: list[str] = [
            "obdscan — saved DTC report",
            f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=== Vehicle ===",
        ]
        for label, value in vehicle.items():
            lines.append(f"{label}: {value}")
        lines.extend(["", "=== Diagnostic Trouble Codes ==="])
        if not rows:
            lines.append("(none reported)")
        else:
            lines.append(f"{'Type':<12} {'Code':<8} Description")
            lines.append("-" * 72)
            for bucket, code in rows:
                desc = lookup_code(self.db, code)
                lines.append(f"{bucket:<12} {code:<8} {desc}")
            lines.append("")
            lines.append(f"Total: {len(rows)} code(s)")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _render_codes(self, rows: list[tuple[str, str]]) -> None:
        if not rows:
            CONSOLE.print(
                Panel(
                    "[green]No DTCs reported.[/]\n[dim]Clear MIL / no faults, or no ECU on the bus.[/]",
                    title="DTCs",
                    border_style="green",
                )
            )
            return
        table = Table(title="Diagnostic Trouble Codes")
        table.add_column("Type", style="cyan")
        table.add_column("Code", style="bold yellow")
        table.add_column("Description")
        for bucket, code in rows:
            table.add_row(bucket, code, lookup_code(self.db, code))
        CONSOLE.print(table)
        CONSOLE.print(f"[dim]{len(rows)} code(s) · {len(self.db)} generic definitions loaded[/]")

    def _query_pid(self, pid: str, fmt) -> str:
        resp = self.session.cmd(f"01{pid}", wait=1.0)
        data = parse_mode01(resp, pid)
        if not data:
            return "—"
        return fmt(data)

    def _live_table(self, pids: list[str]) -> Table:
        table = Table(title="Live data", expand=False)
        table.add_column("PID", style="cyan")
        table.add_column("Value", style="bold")
        table.add_column("Unit")
        for name in pids:
            pid, unit, fmt = PID_CATALOG[name]
            val = self._query_pid(pid, fmt)
            table.add_row(name, val, unit)
        return table

    def _read_vin(self) -> str | None:
        # ISO 15765 multi-frame is messy on dumb ELM; try 0902 best-effort
        resp = self.session.cmd("0902", wait=2.5)
        ascii_chars = []
        hexes = re.findall(r"[0-9A-Fa-f]{2}", resp)
        for h in hexes:
            v = int(h, 16)
            if 32 <= v < 127:
                ascii_chars.append(chr(v))
        vin = "".join(ascii_chars)
        # VIN is 17 chars alphanumeric
        m = re.search(r"[A-HJ-NPR-Z0-9]{17}", vin.upper())
        return m.group(0) if m else (vin.strip() or None)

    def _read_mil(self) -> str | None:
        resp = self.session.cmd("0101", wait=1.2)
        data = parse_mode01(resp, "01")
        if not data:
            return None
        mil = "ON" if data[0] & 0x80 else "OFF"
        return f"{mil} ({data[0] & 0x7F} codes)"

    # --- interactive menu ---------------------------------------------------

    def menu(self) -> None:
        self._banner()
        if not self.session.connected:
            if Confirm.ask(f"Connect to [bold]{self.port}[/] now?", default=True):
                self.connect()

        actions = {
            "1": ("Connection status", lambda: self.show_status()),
            "2": ("Connect / reconnect", lambda: self.connect()),
            "3": ("Disconnect", lambda: self.disconnect()),
            "4": ("Read codes (DTCs)", lambda: self.module_read_codes()),
            "5": ("Clear codes", lambda: self.module_clear_codes()),
            "6": ("Live data", lambda: self.module_live_data()),
            "7": ("Configure live PIDs", lambda: self.module_configure_live()),
            "8": ("List available PIDs", lambda: self.module_pid_list()),
            "9": ("Vehicle info", lambda: self.module_vehicle_info()),
            "10": ("Readiness / MIL", lambda: self.module_readiness()),
            "11": ("Freeze frame", lambda: self.module_freeze_frame()),
            "12": ("Lookup code(s)", lambda: self.module_lookup()),
            "13": ("Raw AT/OBD command", lambda: self.module_raw()),
            "14": ("Enhanced DoIP / manufacturer modules", lambda: self.module_enhanced()),
            "15": ("List manufacturer libraries", lambda: self.module_list_manufacturers()),
            "16": ("Save codes + vehicle info", lambda: self.module_save_codes()),
            "q": ("Quit", None),
        }

        while True:
            CONSOLE.print()
            table = Table(title="obdscan modules", show_header=False, box=None, padding=(0, 2))
            for key, (label, _) in actions.items():
                table.add_row(f"[bold cyan]{key}[/]", label)
            CONSOLE.print(Panel(table, border_style="blue"))
            choice = Prompt.ask("Select", default="4").strip().lower()
            if choice in {"q", "quit", "exit", "0"}:
                self.disconnect()
                return
            if choice not in actions:
                CONSOLE.print("[yellow]Unknown option[/]")
                continue
            label, fn = actions[choice]
            if fn is None:
                continue
            CONSOLE.rule(f"[bold]{label}[/]")
            try:
                fn()
            except ConnectionError as exc:
                CONSOLE.print(f"[red]{exc}[/]")
            except Exception as exc:  # noqa: BLE001 — keep menu alive
                CONSOLE.print(f"[red]Error:[/] {exc}")

    def _banner(self) -> None:
        CONSOLE.print(
            Panel(
                Text.from_markup(
                    "[bold cyan]obdscan[/]  [dim]CLI OBD-II · ELM327 · DoIP manufacturer packs[/]\n"
                    f"[dim]port {self.port} · {len(self.db)} DTC codes · "
                    f"DoIP {'ready' if HAS_DOIP else 'pip install doipclient udsoncan'}[/]"
                ),
                border_style="blue",
            )
        )


# --- argparse / entry -------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="obdscan",
        description="Full-featured CLI OBD-II scanner (interactive menu or subcommands).",
    )
    p.add_argument("-p", "--port", default=DEFAULT_PORT)
    p.add_argument("-b", "--baud", type=int, default=38400)
    p.add_argument("-t", "--timeout", type=float, default=2.0)
    p.add_argument("--dtc-db", default=str(DEFAULT_DTC_DB))

    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("menu", help="Interactive module menu (default)")

    s = sub.add_parser("status", help="Show adapter / ECU status")
    s = sub.add_parser("codes", help="Read DTCs + descriptions")
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("save", help="Save DTCs + vehicle info to Documents/Saved Codes")
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("clear", help="Clear DTCs")
    s.add_argument("--yes", action="store_true")
    s = sub.add_parser("live", help="Stream live data")
    s.add_argument("--once", action="store_true")
    s.add_argument("-i", "--interval", type=float, default=0.4)
    s.add_argument("pids", nargs="*", help="Optional PID names")
    s = sub.add_parser("info", help="Vehicle / adapter info")
    s = sub.add_parser("readiness", help="MIL / monitor readiness")
    s = sub.add_parser("freeze", help="Freeze frame sample")
    s = sub.add_parser("lookup", help="Offline DTC lookup")
    s.add_argument("codes", nargs="+")
    s = sub.add_parser("raw", help="Send raw AT/OBD command")
    s.add_argument("command")
    s = sub.add_parser("pids", help="List built-in live PIDs")

    s = sub.add_parser("manufacturers", help="List manufacturer DoIP/UDS libraries")
    s.add_argument("query", nargs="?", help="Optional search filter")
    s = sub.add_parser("pack", help="Show one manufacturer pack (modules + DIDs)")
    s.add_argument("name", help="Pack id (bmw, vag, mercedes, generic, ...)")

    s = sub.add_parser("doip", help="Enhanced DoIP tools (needs GT327 ethernet + car)")
    dsub = s.add_subparsers(dest="doip_cmd", required=True)
    dsub.add_parser("menu", help="Interactive enhanced DoIP menu")
    dsub.add_parser("discover", help="UDP DoIP vehicle discovery")
    sp = dsub.add_parser("probe", help="Probe manufacturer module LAs on an IP")
    sp.add_argument("-m", "--mfg", default="generic", help="Manufacturer pack id")
    sp.add_argument("--ip", required=True, help="Gateway / ECU IP")
    sp.add_argument("--limit", type=int, default=20, help="Max addresses to probe")
    sr = dsub.add_parser("dids", help="Read pack DIDs from one LA")
    sr.add_argument("-m", "--mfg", default="generic")
    sr.add_argument("--ip", required=True)
    sr.add_argument("--la", required=True, help="Logical address hex, e.g. 1010")
    sd = dsub.add_parser("dtcs", help="Read UDS DTCs from one LA")
    sd.add_argument("-m", "--mfg", default="generic")
    sd.add_argument("--ip", required=True)
    sd.add_argument("--la", required=True)

    return p


def main(argv: list[str] | None = None) -> None:
    # Allow running as script from any cwd
    sys.path.insert(0, str(HERE))
    args = build_parser().parse_args(argv)
    app = App(args.port, args.baud, args.timeout, Path(args.dtc_db))

    cmd = args.cmd or "menu"

    if cmd == "menu":
        app.menu()
        return

    # Offline / DoIP commands — no ELM rfcomm required
    offline = {"lookup", "pids", "manufacturers", "pack", "doip"}
    if cmd not in offline:
        if not app.connect(quiet=False):
            sys.exit(2)

    try:
        if cmd == "status":
            app.show_status()
        elif cmd == "codes":
            app.module_read_codes(force=args.force)
        elif cmd == "save":
            app.module_save_codes(force=args.force)
        elif cmd == "clear":
            app.module_clear_codes(yes=args.yes)
        elif cmd == "live":
            if args.pids:
                app.live_pids = [p.upper() for p in args.pids if p.upper() in PID_CATALOG]
            app.module_live_data(once=args.once, interval=args.interval)
        elif cmd == "info":
            app.module_vehicle_info()
        elif cmd == "readiness":
            app.module_readiness()
        elif cmd == "freeze":
            app.module_freeze_frame()
        elif cmd == "lookup":
            app.module_lookup(args.codes)
        elif cmd == "raw":
            app.module_raw(args.command)
        elif cmd == "pids":
            app.module_pid_list()
        elif cmd == "manufacturers":
            if interactive_enhanced_menu is None:
                CONSOLE.print(f"[red]Import error:[/] {_IMPORT_ERR}")
                sys.exit(1)
            show_manufacturer_list(args.query)
        elif cmd == "pack":
            if interactive_enhanced_menu is None:
                CONSOLE.print(f"[red]Import error:[/] {_IMPORT_ERR}")
                sys.exit(1)
            show_pack_detail(get_pack(args.name))
        elif cmd == "doip":
            _run_doip_cli(args)
        else:
            CONSOLE.print(f"[red]Unknown command:[/] {cmd}")
            sys.exit(1)
    finally:
        if cmd not in offline | {"menu"}:
            app.disconnect()


def _run_doip_cli(args: argparse.Namespace) -> None:
    if interactive_enhanced_menu is None:
        CONSOLE.print(f"[red]Import error:[/] {_IMPORT_ERR}")
        sys.exit(1)
    if not HAS_DOIP:
        CONSOLE.print("[red]Install:[/] pip install doipclient udsoncan")
        sys.exit(1)

    sub = args.doip_cmd
    if sub == "menu":
        interactive_enhanced_menu()
        return
    if sub == "discover":
        vehicles = discover_vehicles(timeout=5.0)
        if not vehicles:
            CONSOLE.print("[yellow]No DoIP vehicles discovered.[/]")
            return
        table = Table(title="DoIP discovery")
        table.add_column("IP")
        table.add_column("LA")
        table.add_column("VIN")
        for v in vehicles:
            table.add_row(v.ip, f"{v.logical_address:#06x}", v.vin or "—")
        CONSOLE.print(table)
        return
    if sub == "probe":
        pack = get_pack(args.mfg)
        addrs = pack.all_addresses()[: args.limit]
        results = probe_pack_modules(pack, args.ip, addresses=addrs)
        table = Table(title=f"Probe {pack.id} @ {args.ip}")
        table.add_column("LA")
        table.add_column("Name")
        table.add_column("Status")
        for la, name, status in results:
            table.add_row(f"{la:#06x}", name, status)
        CONSOLE.print(table)
        return
    if sub in {"dids", "dtcs"}:
        pack = get_pack(args.mfg)
        la = int(args.la, 16)
        with DoipSession(
            pack=pack,
            ip=args.ip,
            logical_address=la,
            client_logical_address=pack.tester_address,
            tcp_port=pack.default_doip_port,
        ) as sess:
            CONSOLE.print(sess.change_session(3))
            if sub == "dids":
                rows = read_interesting_dids(sess, pack.dids)
                table = Table(title="DIDs")
                table.add_column("DID")
                table.add_column("Value")
                for k, v in rows:
                    table.add_row(k, v)
                CONSOLE.print(table)
            else:
                ok, result = sess.read_dtcs()
                if not ok:
                    CONSOLE.print(f"[yellow]{result}[/]")
                elif not result:
                    CONSOLE.print("[green]No DTCs[/]")
                else:
                    for c in result:
                        CONSOLE.print(f"  {c}")
        return
    CONSOLE.print(f"[red]Unknown doip subcommand:[/] {sub}")
    sys.exit(1)


if __name__ == "__main__":
    # Ensure local imports work when executed as ./obdscan.py
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
