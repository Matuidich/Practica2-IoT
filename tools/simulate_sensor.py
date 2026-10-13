"""Emite lecturas de prueba; no representa exactitud ni muestreo físico."""

import argparse
import itertools
import math
import time

from server.protocol import Message
from .simulator_client import SimulatorClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--distances", nargs="+", default=["10", "20", "40", "40.01", "invalid", "50"])
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--repeat", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("El intervalo debe ser positivo y finito.")
    try:
        distances = [None if value == "invalid" else float(value) for value in args.distances]
        if any(value is not None and (not math.isfinite(value) or value <= 0) for value in distances):
            raise ValueError("Las distancias deben ser positivas y finitas.")
        with SimulatorClient(args.host, args.port, "sensor") as client:
            values = itertools.cycle(distances) if args.repeat else distances
            for sequence, distance in enumerate(values, 1):
                fields = {"seq": str(sequence % (2**32))}
                fields.update({"status": "invalid"} if distance is None else {"distance": f"{distance:.2f}"})
                client.send(Message("POST", fields))
                print(f"seq={fields['seq']} distance={distance}", flush=True)
                time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError, EOFError) as error:
        parser.exit(1, f"Simulador sensor: {error}\n")


if __name__ == "__main__":
    main()
