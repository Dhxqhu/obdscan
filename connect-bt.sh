#!/usr/bin/env bash
# Pair/bind GODIAG GT327 (or similar) Bluetooth ELM327 to /dev/rfcomm0
set -euo pipefail
ADDR="${1:-AA:BB:CC:11:22:33}"
RFCOMM_DEV="${RFCOMM_DEV:-0}"

echo "[*] Bluetooth address: $ADDR"
bluetoothctl power on >/dev/null
bluetoothctl trust "$ADDR" >/dev/null || true
bluetoothctl pair "$ADDR" >/dev/null 2>&1 || true
bluetoothctl connect "$ADDR" || true
sleep 1

if [[ -e /dev/rfcomm$RFCOMM_DEV ]]; then
  sudo rfcomm release "$RFCOMM_DEV" 2>/dev/null || true
fi
sudo rfcomm bind "$RFCOMM_DEV" "$ADDR" 1
sudo chmod 666 "/dev/rfcomm$RFCOMM_DEV" 2>/dev/null || true
echo "[*] Bound /dev/rfcomm$RFCOMM_DEV -> $ADDR channel 1"
ls -l "/dev/rfcomm$RFCOMM_DEV"

# quick ATZ smoke test if python serial available
if [[ -x /tools/venv/bin/python ]]; then
  /tools/venv/bin/python - <<PY
import serial, time
ser = serial.Serial("/dev/rfcomm$RFCOMM_DEV", 38400, timeout=2)
time.sleep(0.5)
ser.write(b"ATZ\r")
time.sleep(1.5)
print(ser.read(128))
ser.close()
PY
fi
echo "[*] Done. Run:  ./obdscan"
