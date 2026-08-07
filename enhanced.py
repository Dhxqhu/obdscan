#!/usr/bin/env python3
"""
Enhanced DoIP / manufacturer-module UI helpers for obdscan.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from manufacturers import get_pack, list_packs, search_packs
from manufacturers.base import ManufacturerPack
from doip_session import (
    HAS_DOIP,
    DoipSession,
    discover_vehicles,
    format_did_value,
    probe_pack_modules,
    read_interesting_dids,
)

if TYPE_CHECKING:
    pass

CONSOLE = Console()


def show_manufacturer_list(filter_q: str | None = None) -> None:
    packs = search_packs(filter_q) if filter_q else list_packs()
    table = Table(title="Manufacturer libraries")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Modules", justify="right")
    table.add_column("Transport")
    table.add_column("Maturity")
    for p in packs:
        table.add_row(
            p.id,
            p.name,
            str(len(p.modules)),
            ",".join(p.transports),
            p.maturity,
        )
    CONSOLE.print(table)
    CONSOLE.print(
        "[dim]Packs are address/DID scaffolds from public sources — not dealer databases.[/]"
    )


def show_pack_detail(pack: ManufacturerPack) -> None:
    CONSOLE.print(
        Panel(
            f"[bold]{pack.name}[/] ([cyan]{pack.id}[/])\n"
            f"{pack.description}\n\n"
            f"Tester LA: {pack.tester_address:#06x}  ·  DoIP port {pack.default_doip_port}\n"
            f"IP hints: {', '.join(pack.ip_hints)}\n"
            f"Sources:\n  - " + "\n  - ".join(pack.sources),
            title="Manufacturer pack",
            border_style="blue",
        )
    )
    table = Table(title=f"Modules ({len(pack.modules)})")
    table.add_column("Address", style="yellow")
    table.add_column("Name", style="cyan")
    table.add_column("Mode")
    table.add_column("Description")
    for m in pack.modules:
        table.add_row(m.addr_hex, m.name, m.addressing, m.description)
    CONSOLE.print(table)

    dtable = Table(title=f"DIDs ({len(pack.dids)})")
    dtable.add_column("DID")
    dtable.add_column("Name")
    dtable.add_column("Description")
    for d in pack.dids:
        dtable.add_row(d.did_hex, d.name, d.description)
    CONSOLE.print(dtable)


def pick_pack(default: str = "generic") -> ManufacturerPack | None:
    show_manufacturer_list()
    key = Prompt.ask("Manufacturer id", default=default).strip()
    try:
        return get_pack(key)
    except KeyError as exc:
        CONSOLE.print(f"[red]{exc}[/]")
        return None


def interactive_enhanced_menu() -> None:
    """Submenu: manufacturer DoIP / UDS tools."""
    if not HAS_DOIP:
        CONSOLE.print(
            "[red]DoIP stack missing.[/] Install with:\n"
            "  /tools/venv/bin/pip install doipclient udsoncan"
        )
        return

    pack = pick_pack("bmw")
    if not pack:
        return

    state = {
        "pack": pack,
        "ip": pack.ip_hints[0] if pack.ip_hints else "169.254.1.20",
        "la": pack.gateway_addresses[0] if pack.gateway_addresses else 0x00E0,
    }

    actions = {
        "1": ("Show pack / module list", lambda: show_pack_detail(state["pack"])),
        "2": ("Switch manufacturer", lambda: _switch(state)),
        "3": ("Discover DoIP vehicles (UDP)", lambda: _discover(state)),
        "4": ("Set IP / logical address manually", lambda: _manual_target(state)),
        "5": ("Probe modules on current IP", lambda: _probe(state)),
        "6": ("Connect + read DIDs on selected LA", lambda: _read_dids(state)),
        "7": ("Connect + read UDS DTCs on selected LA", lambda: _read_dtcs(state)),
        "8": ("Connect + clear UDS DTCs on selected LA", lambda: _clear_dtcs(state)),
        "9": ("Raw session control / tester present", lambda: _session_toys(state)),
        "b": ("Back", None),
    }

    while True:
        CONSOLE.print(
            Panel(
                f"Pack [cyan]{state['pack'].id}[/]  IP [yellow]{state['ip']}[/]  "
                f"LA [yellow]{state['la']:#06x}[/] ({state['pack'].resolve_name(state['la'])})",
                title="Enhanced DoIP",
                border_style="magenta",
            )
        )
        table = Table(show_header=False, box=None, padding=(0, 2))
        for k, (label, _) in actions.items():
            table.add_row(f"[bold magenta]{k}[/]", label)
        CONSOLE.print(table)
        choice = Prompt.ask("Enhanced", default="1").strip().lower()
        if choice in {"b", "back", "q"}:
            return
        if choice not in actions or actions[choice][1] is None:
            if choice not in actions:
                CONSOLE.print("[yellow]Unknown[/]")
            continue
        CONSOLE.rule(actions[choice][0])
        try:
            actions[choice][1]()
        except Exception as exc:  # noqa: BLE001
            CONSOLE.print(f"[red]{exc}[/]")


def _switch(state: dict) -> None:
    pack = pick_pack(state["pack"].id)
    if pack:
        state["pack"] = pack
        state["ip"] = pack.ip_hints[0]
        state["la"] = pack.gateway_addresses[0] if pack.gateway_addresses else state["la"]


def _discover(state: dict) -> None:
    CONSOLE.print("[cyan]Broadcasting DoIP vehicle identification…[/]")
    CONSOLE.print("[dim]GT327: flip DoIP/ENET switch ON, car powered, ethernet linked.[/]")
    vehicles = discover_vehicles(timeout=5.0)
    if not vehicles:
        CONSOLE.print("[yellow]No DoIP announcements heard.[/]")
        return
    table = Table(title="Discovered DoIP entities")
    table.add_column("#")
    table.add_column("IP")
    table.add_column("LA")
    table.add_column("VIN")
    for i, v in enumerate(vehicles, 1):
        table.add_row(str(i), v.ip, f"{v.logical_address:#06x}", v.vin or "—")
    CONSOLE.print(table)
    if sys.stdin.isatty() and Confirm.ask("Use first result?", default=True):
        v = vehicles[0]
        state["ip"] = v.ip
        state["la"] = v.logical_address


def _manual_target(state: dict) -> None:
    state["ip"] = Prompt.ask("ECU / gateway IP", default=state["ip"])
    raw = Prompt.ask("Logical address (hex)", default=f"{state['la']:X}")
    state["la"] = int(raw, 16)


def _probe(state: dict) -> None:
    pack: ManufacturerPack = state["pack"]
    CONSOLE.print(
        f"[cyan]Probing {len(pack.modules)} module LAs on {state['ip']}[/] "
        "[dim](slow — timeouts expected for missing ECUs)[/]"
    )
    # Limit interactive probe to gateways + first N modules unless user forces all
    addrs = list(pack.gateway_addresses)
    for m in pack.modules:
        if m.address not in addrs:
            addrs.append(m.address)
        if len(addrs) >= 12 and sys.stdin.isatty():
            if not Confirm.ask(
                f"Probe first 12 only (of {len(pack.all_addresses())})?", default=True
            ):
                addrs = pack.all_addresses()
            break
    results = probe_pack_modules(pack, state["ip"], addresses=addrs[:40], timeout_each=1.2)
    table = Table(title="Module probe")
    table.add_column("LA")
    table.add_column("Name")
    table.add_column("Status")
    alive = []
    for la, name, status in results:
        style = "green" if status == "alive" else "dim"
        table.add_row(f"{la:#06x}", name, f"[{style}]{status}[/]")
        if status == "alive":
            alive.append(la)
    CONSOLE.print(table)
    if alive and Confirm.ask(f"Select first alive LA {alive[0]:#06x}?", default=True):
        state["la"] = alive[0]


def _read_dids(state: dict) -> None:
    pack: ManufacturerPack = state["pack"]
    with DoipSession(
        pack=pack,
        ip=state["ip"],
        logical_address=state["la"],
        client_logical_address=pack.tester_address,
        tcp_port=pack.default_doip_port,
    ) as sess:
        CONSOLE.print(sess.change_session(3))
        rows = read_interesting_dids(sess, pack.dids)
    table = Table(title=f"DIDs @ {state['la']:#06x}")
    table.add_column("DID")
    table.add_column("Value")
    for k, v in rows:
        table.add_row(k, v)
    CONSOLE.print(table)


def _read_dtcs(state: dict) -> None:
    pack: ManufacturerPack = state["pack"]
    with DoipSession(
        pack=pack,
        ip=state["ip"],
        logical_address=state["la"],
        client_logical_address=pack.tester_address,
        tcp_port=pack.default_doip_port,
    ) as sess:
        sess.change_session(3)
        ok, result = sess.read_dtcs()
    if not ok:
        CONSOLE.print(f"[yellow]{result}[/]")
        return
    if not result:
        CONSOLE.print("[green]No UDS DTCs returned.[/]")
        return
    table = Table(title="UDS DTCs")
    table.add_column("Code")
    for c in result:
        table.add_row(str(c))
    CONSOLE.print(table)


def _clear_dtcs(state: dict) -> None:
    if not Confirm.ask("[yellow]Clear UDS DTCs on this ECU?[/]", default=False):
        return
    pack: ManufacturerPack = state["pack"]
    with DoipSession(
        pack=pack,
        ip=state["ip"],
        logical_address=state["la"],
        client_logical_address=pack.tester_address,
        tcp_port=pack.default_doip_port,
    ) as sess:
        sess.change_session(3)
        ok, msg = sess.clear_dtcs()
    CONSOLE.print(("[green]" if ok else "[red]") + msg + "[/]")


def _session_toys(state: dict) -> None:
    pack: ManufacturerPack = state["pack"]
    with DoipSession(
        pack=pack,
        ip=state["ip"],
        logical_address=state["la"],
        client_logical_address=pack.tester_address,
        tcp_port=pack.default_doip_port,
    ) as sess:
        CONSOLE.print("default:", sess.change_session(1))
        CONSOLE.print("extended:", sess.change_session(3))
        CONSOLE.print("tester_present:", sess.tester_present())
