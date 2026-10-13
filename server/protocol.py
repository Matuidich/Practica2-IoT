"""Contrato de mensajes compartido con los clientes C++ y los simuladores."""

from dataclasses import dataclass
import math
import re

MAX_LINE_BYTES = 256
LED_KEYS = ("redLed", "yellowLed", "greenLed")
LED_MODES = frozenset(("on", "off", "blink_2", "blink_4"))
ROLES = frozenset(("sensor", "actuator"))
ERROR_CODES = frozenset((
    "BAD_MESSAGE", "LINE_TOO_LONG", "REGISTER_REQUIRED", "REGISTER_TIMEOUT",
    "ROLE_IN_USE", "WRONG_ROLE", "ALREADY_REGISTERED", "UNSUPPORTED_VERSION",
))


class ProtocolError(ValueError):
    """Error con un código que se puede transmitir sin exponer excepciones."""

    def __init__(self, code: str = "BAD_MESSAGE") -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Message:
    command: str
    args: dict[str, str]

    @property
    def sequence(self) -> int | None:
        value = self.args.get("seq")
        return None if value is None else int(value)


class LineBuffer:
    """Extrae líneas completas y conserva fragmentos con memoria acotada."""

    def __init__(self) -> None:
        self._pending = bytearray()

    def feed(self, data: bytes) -> list[str]:
        lines: list[str] = []
        for byte in data:
            if byte == 10:
                payload = bytes(self._pending)
                self._pending.clear()
                if payload.endswith(b"\r"):
                    payload = payload[:-1]
                if len(payload) > MAX_LINE_BYTES:
                    raise ProtocolError("LINE_TOO_LONG")
                try:
                    lines.append(payload.decode("ascii"))
                except UnicodeDecodeError as error:
                    raise ProtocolError() from error
            else:
                self._pending.append(byte)
                # Permit a trailing CR only as the extra byte of a CRLF terminator.
                if len(self._pending) > MAX_LINE_BYTES + 1 or (
                    len(self._pending) == MAX_LINE_BYTES + 1 and byte != 13
                ):
                    self._pending.clear()
                    raise ProtocolError("LINE_TOO_LONG")
        return lines


class ProtocolCodec:
    """Acepta los formatos del informe y metadatos opcionales de diagnóstico."""

    @staticmethod
    def parse(line: str) -> Message:
        if not line or len(line) > MAX_LINE_BYTES:
            raise ProtocolError()
        if any(ord(char) < 32 or ord(char) > 126 for char in line):
            raise ProtocolError()
        parts = line.replace(",", " ").split()
        if not parts:
            raise ProtocolError()
        command = parts[0]
        args: dict[str, str] = {}
        for token in parts[1:]:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*=[A-Za-z0-9_.+-]+", token):
                raise ProtocolError()
            key, value = token.split("=", 1)
            if key in args:
                raise ProtocolError()
            args[key] = value

        if "seq" in args:
            if not re.fullmatch(r"[0-9]+", args["seq"]) or int(args["seq"]) > 0xFFFFFFFF:
                raise ProtocolError()
        keys = set(args)
        if command in ("REGISTER", "OK"):
            if not {"type"} <= keys <= {"type", "version"} or args["type"] not in ROLES:
                raise ProtocolError()
            if args.get("version", "1") != "1":
                raise ProtocolError("UNSUPPORTED_VERSION")
        elif command == "POST":
            payload_keys = keys - {"seq"}
            if payload_keys == {"distance"}:
                value = args["distance"]
                if not re.fullmatch(r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", value):
                    raise ProtocolError()
                distance = float(value)
                if not math.isfinite(distance) or distance <= 0:
                    raise ProtocolError()
            elif payload_keys != {"status"} or args["status"] != "invalid":
                raise ProtocolError()
        elif command == "SET":
            if keys - {"seq"} != set(LED_KEYS):
                raise ProtocolError()
            if any(args[key] not in LED_MODES for key in LED_KEYS):
                raise ProtocolError()
        elif command == "APPLIED":
            if keys - {"seq"}:
                raise ProtocolError()
        elif command == "ERROR":
            if keys != {"code"} or args["code"] not in ERROR_CODES:
                raise ProtocolError()
        else:
            raise ProtocolError()
        return Message(command, args)

    @classmethod
    def encode(cls, message: Message) -> bytes:
        if message.command == "SET":
            prefix = "SET "
            if "seq" in message.args:
                prefix += f"seq={message.args['seq']} "
            line = prefix + ", ".join(f"{key}={message.args[key]}" for key in LED_KEYS)
        else:
            line = " ".join((message.command, *(f"{key}={value}" for key, value in message.args.items())))
        cls.parse(line)
        return (line + "\n").encode("ascii")
