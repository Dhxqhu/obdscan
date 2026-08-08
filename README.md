# obdscan

CLI OBD-II scanner for ELM327 dongles (e.g. GODIAG GT327) plus enhanced **DoIP/UDS** manufacturer packs for ethernet-capable adapters.

This is a basic CLI program to communicate with the cheap GODIAG GT327. Similar to the Ubuntu package obdscan that works with the elm327 but the gt327 also has DoIP ethernet fuction that this program also takes advantage of. Not much testing has been done yet. No gui is planned as I personally prefer cli.

- Bluetooth ELM → SAE OBD-II (codes, live PIDs, readiness, freeze frame, …)
- DoIP ethernet → OEM module scaffolds (Toyota, Ford, Chevy, BMW, …)

## Install

### 1. Clone

```bash
git clone https://github.com/Dhxqhu/obdscan.git
cd obdscan
```

### 2. System packages (Debian / Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip bluez bluez-tools rfkill
```

Bluetooth binding also needs `rfcomm` (usually from `bluez`).

### 3. Python deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Optional: put `obdscan` on your PATH

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/obdscan" ~/.local/bin/obdscan
# ensure ~/.local/bin is on PATH, then:
obdscan --help
```

Without the symlink, always run `./obdscan` from the repo (with the venv activated).

### 5. Bluetooth MAC (GT327)

Edit the default address in `connect-bt.sh`, or pass it:

```bash
./connect-bt.sh AA:BB:CC:11:22:33
```

## Quick start — Bluetooth (ELM327)

```bash
source .venv/bin/activate
./connect-bt.sh                 # once per boot
./obdscan                       # interactive menu
```

Port override: `-p /dev/rfcomm0` or `OBD_PORT=/dev/rfcomm0`.

## Quick start — Ethernet DoIP (GT327 ENET)

Needs a DoIP-capable car, GT327 DoIP/ENET switch on, and ethernet linked to the laptop.

```bash
source .venv/bin/activate
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
| 16 | Save codes + vehicle info → `~/Documents/Saved Codes/` |
| q | Quit |

## Subcommands

```bash
./obdscan codes
./obdscan save
./obdscan live --once RPM SPEED COOLANT
./obdscan info
./obdscan readiness
./obdscan lookup P0420
./obdscan manufacturers
./obdscan pack chevy
./obdscan doip discover
./obdscan doip probe -m toyota --ip 169.254.1.20
```

Saved reports land in `~/Documents/Saved Codes/` as timestamped `.txt` files (VIN included in the filename when available).
## Notes

Manufacturer packs are **address/DID scaffolds** from public sources — not dealer databases (ODIS/ISTA/Xentry). Many logical addresses will time out; that is expected.

See [manufacturers/README.md](manufacturers/README.md) for brand IDs.
