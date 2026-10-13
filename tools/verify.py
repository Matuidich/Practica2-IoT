"""Verificación local y de CI, usando siempre el intérprete activo."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--software-only", action="store_true", help="Omite solamente la compilación ESP32")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.setdefault("PLATFORMIO_CORE_DIR", str(root / ".tools/platformio"))
    commands = [
        ["-m", "unittest", "discover", "-s", "server/tests", "-v"],
        ["-m", "tools.test_firmware"],
        ["-m", "tools.smoke_test", "--duration", "5"],
    ]
    if not args.software_only:
        commands.append(["-m", "platformio", "run", "-d", "firmware", "-e", "sensor", "-e", "actuator"])
    for command in commands:
        print("Ejecutando: python " + " ".join(command), flush=True)
        result = subprocess.run([sys.executable, *command], cwd=root, env=environment)
        if result.returncode:
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
