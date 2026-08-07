# obdscan

CLI OBD-II scanner for ELM327 dongles (e.g. GODIAG GT327) plus enhanced **DoIP/UDS** manufacturer packs for ethernet-capable adapters.

- Bluetooth ELM → SAE OBD-II (codes, live PIDs, readiness, freeze frame, …)
- DoIP ethernet → OEM module scaffolds (Toyota, Ford, Chevy, BMW, …)

## Install

```bash
git clone https://github.com/Dhxqhu/obdscan.git
cd obdscan
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: put the wrapper on your PATH:

```bash
ln -sf "$(pwd)/obdscan" ~/.local/bin/obdscan
```

## Bluetooth (ELM327)

```bash
./connect-bt.sh                 # once per boot (edit MAC if needed)
./obdscan                       # interactive menu
# or
OBD_PORT=/dev/rfcomm0 ./obdscan codes
```

## Ethernet DoIP (GT327 ENET mode)

Needs a DoIP-capable car + adapter DoIP/ENET switch on + ethernet link.

```bash
./obdscan                       # menu → 14 Enhanced DoIP
# or
./obdscan doip menu
./obdscan doip discover
./obdscan manufacturers
./obdscan pack toyota
```

## Interactive menu

| # | Module |
|---|--------|
| 1–3 | Connection status / connect / disconnect |
| 4 | Read codes + SAE descriptions |
| 5 | Clear codes |
| 6–8 | Live data / configure PIDs / list PIDs |
| 9 | Vehicle info |
| 10 | Readiness / MIL monitors |
| 11 | Freeze frame |
| 12 | Offline DTC lookup |
| 13 | Raw AT/OBD |
| 14 | Enhanced DoIP / manufacturer packs |
| 15 | List manufacturer libraries |
| q | Quit |

## Subcommands

```bash
./obdscan codes
./obdscan live --once RPM SPEED COOLANT
./obdscan info
./obdscan readiness
./obdscan lookup P0420
./obdscan manufacturers
./obdscan pack chevy
./obdscan doip discover
./obdscan doip probe -m toyota --ip 169.254.1.20
```

Port override: `-p /dev/rfcomm0` or `OBD_PORT=...`

## Notes

Manufacturer packs are **address/DID scaffolds** from public sources — not dealer databases (ODIS/ISTA/Xentry). Many logical addresses will time out; that is expected.

See [manufacturers/README.md](manufacturers/README.md) for brand IDs.
