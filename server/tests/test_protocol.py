import json
from pathlib import Path
import unittest

from server.protocol import LineBuffer, Message, ProtocolCodec, ProtocolError


class ProtocolTests(unittest.TestCase):
    def test_shared_contract(self):
        path = Path(__file__).resolve().parents[2] / "contracts/protocol-cases.json"
        for case in json.loads(path.read_text(encoding="utf-8")):
            with self.subTest(case=case["name"]):
                if case["valid"]:
                    message = ProtocolCodec.parse(case["line"])
                    self.assertEqual(message.command, case["command"])
                    encoded = ProtocolCodec.encode(message)
                    self.assertEqual(ProtocolCodec.parse(encoded.decode("ascii").rstrip("\n")), message)
                else:
                    with self.assertRaises(ProtocolError):
                        ProtocolCodec.parse(case["line"])

    def test_fragmented_and_coalesced_lines(self):
        buffer = LineBuffer()
        self.assertEqual(buffer.feed(b"REGIS"), [])
        self.assertEqual(buffer.feed(b"TER type=sensor\nPOST distance=2"), ["REGISTER type=sensor"])
        self.assertEqual(buffer.feed(b"0\r\nPOST distance=40\n"), ["POST distance=20", "POST distance=40"])

    def test_limit_with_crlf(self):
        buffer = LineBuffer()
        self.assertEqual(buffer.feed(b"x" * 256 + b"\r"), [])
        self.assertEqual(buffer.feed(b"\n"), ["x" * 256])

    def test_overflow_without_terminator(self):
        with self.assertRaises(ProtocolError) as error:
            LineBuffer().feed(b"x" * 257)
        self.assertEqual(error.exception.code, "LINE_TOO_LONG")

    def test_non_ascii_is_rejected(self):
        with self.assertRaises(ProtocolError):
            LineBuffer().feed(b"POST distance=\xff\n")

    def test_set_format_matches_report(self):
        message = Message("SET", {"redLed": "blink_4", "yellowLed": "off", "greenLed": "off"})
        self.assertEqual(ProtocolCodec.encode(message), b"SET redLed=blink_4, yellowLed=off, greenLed=off\n")
