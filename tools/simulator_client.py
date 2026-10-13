"""Cliente de consola con el mismo contrato TCP que los ESP32."""

from collections import deque
import socket
import time

from server.protocol import LineBuffer, Message, ProtocolCodec, ProtocolError


class SimulatorClient:
    def __init__(self, host: str, port: int, role: str) -> None:
        self.connection = socket.create_connection((host, port), timeout=3)
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buffer = LineBuffer()
        self.pending: deque[Message] = deque()
        try:
            self.send(Message("REGISTER", {"type": role, "version": "1"}))
            reply = self.receive()
            if reply.command != "OK" or reply.args.get("type") != role:
                raise ProtocolError(reply.args.get("code", "BAD_MESSAGE"))
        except Exception:
            self.connection.close()
            raise

    def send(self, message: Message) -> None:
        self.connection.sendall(ProtocolCodec.encode(message))

    def receive(self, timeout: float = 3.0) -> Message:
        deadline = time.monotonic() + timeout
        while not self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout()
            self.connection.settimeout(remaining)
            data = self.connection.recv(1024)
            if not data:
                raise EOFError("El servidor cerró la conexión.")
            self.pending.extend(ProtocolCodec.parse(line) for line in self.buffer.feed(data))
        return self.pending.popleft()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SimulatorClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
