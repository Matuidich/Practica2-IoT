"""Dos roles TCP persistentes, recepción delimitada y apagado por datos vencidos."""

import json
import logging
import socket
import threading
import time
import uuid

from .config import ServerConfig
from .controller import ControlService
from .protocol import LineBuffer, Message, ProtocolCodec, ProtocolError

LOGGER = logging.getLogger("iot.server")


class DeviceRegistry:
    """Asocia cada rol a una sesión; elimina solamente la misma sesión registrada."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._devices: dict[str, ClientSession] = {}

    def register(self, role: str, session: "ClientSession") -> bool:
        with self._lock:
            if role in self._devices:
                return False
            self._devices[role] = session
            return True

    def get(self, role: str) -> "ClientSession | None":
        with self._lock:
            return self._devices.get(role)

    def remove(self, session: "ClientSession") -> None:
        with self._lock:
            if self._devices.get(session.role) is session:
                del self._devices[session.role]


class ClientSession:
    def __init__(self, server: "TcpServer", connection: socket.socket, address: tuple) -> None:
        self.server = server
        self.connection = connection
        self.address = address
        self.id = uuid.uuid4().hex[:12]
        self.role: str | None = None
        self.opened_at = time.monotonic()
        self._send_lock = threading.Lock()
        self._closed = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"client-{self.id}", daemon=True)

    def start(self) -> None:
        self.connection.settimeout(self.server.config.io_timeout)
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._thread.start()

    def send(self, message: Message) -> bool:
        data = ProtocolCodec.encode(message)
        with self._send_lock:
            if self._closed.is_set():
                return False
            try:
                self.connection.sendall(data)
                return True
            except OSError:
                self.close()
                return False

    def close(self) -> None:
        self._closed.set()
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.connection.close()

    def join(self) -> None:
        if self._thread.ident is not None and threading.current_thread() is not self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        buffer = LineBuffer()
        try:
            while not self._closed.is_set() and not self.server.stopped.is_set():
                if self.role is None and time.monotonic() - self.opened_at > self.server.config.register_timeout:
                    self.send(Message("ERROR", {"code": "REGISTER_TIMEOUT"}))
                    break
                try:
                    data = self.connection.recv(1024)
                except socket.timeout:
                    continue
                if not data:
                    break
                try:
                    lines = buffer.feed(data)
                except ProtocolError as error:
                    self.send(Message("ERROR", {"code": error.code}))
                    break
                for line in lines:
                    if self._closed.is_set():
                        break
                    try:
                        self.server.handle(self, ProtocolCodec.parse(line))
                    except ProtocolError as error:
                        self.server.event("protocol_error", session=self.id, role=self.role, code=error.code)
                        self.send(Message("ERROR", {"code": error.code}))
        except OSError:
            pass
        finally:
            self.close()
            self.server.disconnected(self)


class TcpServer:
    def __init__(self, config: ServerConfig | None = None) -> None:
        self.config = config or ServerConfig()
        self.registry = DeviceRegistry()
        self.control = ControlService()
        self.stopped = threading.Event()
        self._sessions: set[ClientSession] = set()
        self._sessions_lock = threading.Lock()
        self._control_lock = threading.RLock()
        self._last_measurement: float | None = None
        self._safe_state = True
        self._listener: socket.socket | None = None
        self._threads: list[threading.Thread] = []
        self.address: tuple[str, int] | None = None

    @staticmethod
    def event(name: str, **fields: object) -> None:
        LOGGER.info(json.dumps({"event": name, "time": time.time(), **fields}, ensure_ascii=True))

    def start(self) -> "TcpServer":
        if self._listener is not None or self.stopped.is_set():
            raise RuntimeError("Crear una nueva instancia para iniciar el servidor de nuevo.")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.config.host, self.config.port))
            listener.listen(8)
            listener.settimeout(self.config.io_timeout)
        except OSError:
            listener.close()
            raise
        self._listener = listener
        self.address = listener.getsockname()
        for target, name in ((self._accept_loop, "tcp-accept"), (self._watchdog, "tcp-watchdog")):
            thread = threading.Thread(target=target, name=name, daemon=True)
            self._threads.append(thread)
            thread.start()
        self.event("server_started", host=self.address[0], port=self.address[1])
        return self

    def stop(self) -> None:
        self.stopped.set()
        if self._listener is not None:
            self._listener.close()
        for thread in self._threads:
            thread.join(timeout=2)
        with self._sessions_lock:
            sessions = tuple(self._sessions)
        for session in sessions:
            session.close()
        for session in sessions:
            session.join()

    def __enter__(self) -> "TcpServer":
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.stop()

    def _accept_loop(self) -> None:
        assert self._listener is not None
        while not self.stopped.is_set():
            try:
                connection, address = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            session = ClientSession(self, connection, address)
            with self._sessions_lock:
                self._sessions.add(session)
            session.start()
            self.event("connected", session=session.id, peer=address[0])

    def handle(self, session: ClientSession, message: Message) -> None:
        with self._control_lock:
            if message.command == "REGISTER":
                if session.role is not None:
                    raise ProtocolError("ALREADY_REGISTERED")
                role = message.args["type"]
                if not self.registry.register(role, session):
                    session.send(Message("ERROR", {"code": "ROLE_IN_USE"}))
                    session.close()
                    return
                session.role = role
                response = {"type": role}
                if "version" in message.args:
                    response["version"] = "1"
                session.send(Message("OK", response))
                self.event("registered", session=session.id, role=role)
                if role == "sensor":
                    self._last_measurement = None
                else:
                    self._safe_state = True
                    session.send(self.control.command_for(None))
                return
            if session.role is None:
                raise ProtocolError("REGISTER_REQUIRED")
            if message.command == "POST" and session.role == "sensor":
                distance = float(message.args["distance"]) if "distance" in message.args else None
                self._last_measurement = time.monotonic()
                command = self.control.command_for(distance, message.sequence)
                actuator = self.registry.get("actuator")
                delivered = actuator is not None and actuator.send(command)
                if delivered:
                    self._safe_state = distance is None
                self.event("measurement", session=session.id, role=session.role, seq=message.sequence,
                           distance_cm=distance, state=self.control.classifier.classify(distance).value,
                           delivered=delivered)
            elif message.command == "APPLIED" and session.role == "actuator":
                self.event("applied", session=session.id, role=session.role, seq=message.sequence)
            else:
                raise ProtocolError("WRONG_ROLE")

    def disconnected(self, session: ClientSession) -> None:
        with self._control_lock:
            was_sensor = self.registry.get("sensor") is session
            self.registry.remove(session)
            if was_sensor:
                self._last_measurement = None
                self._turn_off("sensor_disconnected")
        with self._sessions_lock:
            self._sessions.discard(session)
        self.event("disconnected", session=session.id, role=session.role)

    def _turn_off(self, reason: str) -> None:
        actuator = self.registry.get("actuator")
        if actuator is not None and not self._safe_state:
            actuator.send(self.control.command_for(None))
            self.event("safe_state", reason=reason)
        self._safe_state = True

    def _watchdog(self) -> None:
        while not self.stopped.wait(min(0.05, self.config.stale_after / 4)):
            with self._control_lock:
                if self._last_measurement is not None and time.monotonic() - self._last_measurement >= self.config.stale_after:
                    self._turn_off("measurement_timeout")
