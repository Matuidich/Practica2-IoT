"""Recorre dos clientes TCP reales en loopback durante un intervalo acotado."""

import argparse
import json
import math
import time

from server.config import ServerConfig
from server.protocol import Message
from server.tcp_server import TcpServer
from .simulator_client import SimulatorClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=5)
    parser.add_argument("--interval", type=float, default=0.25)
    args = parser.parse_args()
    if any(not math.isfinite(value) or value <= 0 for value in (args.duration, args.interval)):
        parser.error("Duración e intervalo deben ser positivos y finitos.")
    samples = [(10, "redLed", "blink_4"), (20, "yellowLed", "on"), (40, "yellowLed", "on"),
               (40.01, "greenLed", "on"), (None, "redLed", "off")]
    latencies = []
    with TcpServer(ServerConfig(host="127.0.0.1", port=0, stale_after=max(2, args.interval * 4))) as server:
        with SimulatorClient(*server.address, "actuator") as actuator, SimulatorClient(*server.address, "sensor") as sensor:
            actuator.receive()  # Initial off command; no old measurement is replayed.
            started = time.monotonic()
            sequence = 0
            next_sample = started
            while time.monotonic() - started < args.duration:
                sequence += 1
                distance, key, mode = samples[(sequence - 1) % len(samples)]
                fields = {"seq": str(sequence % (2**32))}
                fields.update({"status": "invalid"} if distance is None else {"distance": str(distance)})
                before = time.monotonic()
                sensor.send(Message("POST", fields))
                command = actuator.receive()
                if command.sequence != sequence % (2**32) or command.args[key] != mode:
                    raise AssertionError(f"Actuación inesperada: {command}")
                actuator.send(Message("APPLIED", {"seq": fields["seq"]}))
                latencies.append((time.monotonic() - before) * 1000)
                next_sample += args.interval
                time.sleep(max(0, next_sample - time.monotonic()))
            elapsed = time.monotonic() - started
    print(json.dumps({"scope": "software_loopback", "duration_s": round(elapsed, 3), "messages": sequence,
                      "messages_per_s": round(sequence / elapsed, 3), "max_exchange_ms": round(max(latencies), 3),
                      "physical_requirements_verified": False}, indent=2))


if __name__ == "__main__":
    main()
