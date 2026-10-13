"""Muestra estados lógicos de LEDs; las señales físicas se prueban en el ESP32."""

import argparse
import json
import math
import socket
import time

from server.protocol import LED_KEYS, Message
from .simulator_client import SimulatorClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--duration", type=float, default=0, help="Segundos; 0 ejecuta hasta Ctrl+C")
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error("La duración debe ser finita y no negativa.")
    started = last_command = time.monotonic()
    state = dict.fromkeys(LED_KEYS, "off")
    try:
        with SimulatorClient(args.host, args.port, "actuator") as client:
            while not args.duration or time.monotonic() - started < args.duration:
                try:
                    command = client.receive(timeout=0.1)
                except socket.timeout:
                    if time.monotonic() - last_command >= 2 and any(value != "off" for value in state.values()):
                        state = dict.fromkeys(LED_KEYS, "off")
                        print(json.dumps({"event": "simulated_safe_state", "leds": state}), flush=True)
                    continue
                if command.command == "ERROR":
                    raise ValueError(command.args["code"])
                if command.command != "SET":
                    raise ValueError("Se esperaba un comando SET.")
                state = {key: command.args[key] for key in LED_KEYS}
                last_command = time.monotonic()
                client.send(Message("APPLIED", {"seq": command.args["seq"]} if command.sequence is not None else {}))
                print(json.dumps({"event": "simulated_actuation", "seq": command.sequence, "leds": state}), flush=True)
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError, EOFError) as error:
        parser.exit(1, f"Simulador actuador: {error}\n")


if __name__ == "__main__":
    main()
