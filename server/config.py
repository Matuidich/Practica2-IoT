"""Parámetros de ejecución configurables desde la línea de comandos."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 5000
    stale_after: float = 2.0
    register_timeout: float = 3.0
    io_timeout: float = 0.2

    def __post_init__(self) -> None:
        if not 0 <= self.port <= 65535:
            raise ValueError("El puerto debe estar entre 0 y 65535.")
        for value in (self.stale_after, self.register_timeout, self.io_timeout):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Los timeouts deben ser positivos y finitos.")
