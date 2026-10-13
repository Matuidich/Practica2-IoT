"""Entrada: python -m server --host 0.0.0.0 --port 5000."""

import argparse
import logging
from pathlib import Path

from .config import ServerConfig
from .tcp_server import TcpServer


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor TCP de objetos inteligentes")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--stale-after", type=float, default=2.0)
    parser.add_argument("--log-file", type=Path, help="Archivo JSON Lines adicional")
    args = parser.parse_args()
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if args.log_file:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=handlers)
    try:
        config = ServerConfig(host=args.host, port=args.port, stale_after=args.stale_after)
        with TcpServer(config) as server:
            server.stopped.wait()
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError) as error:
        parser.exit(1, f"No se pudo iniciar el servidor: {error}\n")


if __name__ == "__main__":
    main()
