"""Captura muestras reales del firmware sensor en CSV para las validaciones."""

import argparse
import csv
import math
from pathlib import Path
import re
import time

FIELDS = ("seq", "sensor_time_ms", "distance_cm", "valid", "sent", "reference_cm")
SAMPLE = re.compile(r"sample seq=([0-9]+) t_ms=([0-9]+) distance_cm=([0-9]+(?:\.[0-9]+)?) valid=([01]) sent=([01])")


def parse_sample(line: str, reference: float | None = None) -> dict[str, object] | None:
    match = SAMPLE.fullmatch(line.strip())
    if not match:
        return None
    sequence, timestamp, distance, valid, sent = match.groups()
    return dict(zip(FIELDS, (int(sequence), int(timestamp), float(distance), int(valid), int(sent),
                            "" if reference is None else reference)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--reference-cm", type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("La duración debe ser positiva y finita.")
    if args.reference_cm is not None and (not math.isfinite(args.reference_cm) or args.reference_cm <= 0):
        parser.error("La referencia debe ser positiva y finita.")
    try:
        import serial
    except ImportError:
        parser.exit(1, "Instalar las herramientas con pip install -r requirements-dev.txt.\n")
    count = 0
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Refuse to overwrite evidence from a previous run.
        with args.output.open("x", newline="", encoding="utf-8") as file, serial.Serial(args.port, 115200, timeout=0.2) as port:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            started = time.monotonic()
            while time.monotonic() - started < args.seconds:
                line = port.readline().decode("ascii", errors="replace")
                row = parse_sample(line, args.reference_cm)
                if row is not None:
                    writer.writerow(row)
                    file.flush()
                    count += 1
    except (OSError, ValueError) as error:
        parser.exit(1, f"Captura serial: {error}\n")
    if not count:
        parser.exit(1, "No se capturaron muestras; revisar puerto, firmware y conexión serial.\n")
    print(f"Capturadas {count} muestras reales en {args.output}.")


if __name__ == "__main__":
    main()
