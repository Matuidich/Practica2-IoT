from collections import deque
import socket
import time
import unittest

from server.config import ServerConfig
from server.protocol import LineBuffer, ProtocolCodec
from server.tcp_server import TcpServer


class Peer:
    def __init__(self, address):
        self.socket = socket.create_connection(address, timeout=1)
        self.buffer = LineBuffer()
        self.messages = deque()

    def send(self, line):
        self.socket.sendall((line + "\n").encode("ascii"))

    def receive(self):
        while not self.messages:
            data = self.socket.recv(1024)
            if not data:
                raise EOFError("Conexión cerrada")
            self.messages.extend(ProtocolCodec.parse(line) for line in self.buffer.feed(data))
        return self.messages.popleft()

    def close(self):
        self.socket.close()


class TcpServerTests(unittest.TestCase):
    def setUp(self):
        self.server = TcpServer(ServerConfig(host="127.0.0.1", port=0, stale_after=0.3, register_timeout=0.3, io_timeout=0.05)).start()
        self.peers = []

    def tearDown(self):
        for peer in self.peers:
            peer.close()
        self.server.stop()

    def peer(self, role=None, metadata=False):
        peer = Peer(self.server.address)
        self.peers.append(peer)
        if role:
            peer.send(f"REGISTER type={role}" + (" version=1" if metadata else ""))
            self.assertEqual(peer.receive().command, "OK")
            if role == "actuator":
                self.assert_all_off(peer.receive())
        return peer

    def assert_all_off(self, message):
        self.assertEqual(message.command, "SET")
        for key in ("redLed", "yellowLed", "greenLed"):
            self.assertEqual(message.args[key], "off")

    def wait_unregistered(self, role):
        deadline = time.monotonic() + 1
        while self.server.registry.get(role) is not None and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertIsNone(self.server.registry.get(role))

    def test_report_messages_and_all_boundaries(self):
        actuator = self.peer("actuator")
        sensor = self.peer("sensor")
        for distance, key, mode in ((19.99, "redLed", "blink_4"), (20, "yellowLed", "on"), (40, "yellowLed", "on"), (40.01, "greenLed", "on")):
            sensor.send(f"POST distance={distance}")
            command = actuator.receive()
            self.assertEqual(command.args[key], mode)
            self.assertNotIn("seq", command.args)

    def test_metadata_and_applied_acknowledgment(self):
        actuator = self.peer("actuator", metadata=True)
        sensor = self.peer("sensor", metadata=True)
        sensor.send("POST seq=42 distance=10")
        self.assertEqual(actuator.receive().sequence, 42)
        actuator.send("APPLIED seq=42")
        sensor.send("POST seq=43 distance=50")
        self.assertEqual(actuator.receive().sequence, 43)

    def test_partial_registration_and_multiple_posts(self):
        actuator = self.peer("actuator")
        sensor = self.peer()
        sensor.socket.sendall(b"REGIS")
        sensor.socket.sendall(b"TER type=sensor\r\nPOST distance=10\nPOST distance=50\n")
        self.assertEqual(sensor.receive().command, "OK")
        self.assertEqual(actuator.receive().args["redLed"], "blink_4")
        self.assertEqual(actuator.receive().args["greenLed"], "on")

    def test_invalid_measurement_is_a_distinct_safe_state(self):
        actuator = self.peer("actuator")
        sensor = self.peer("sensor")
        sensor.send("POST distance=50")
        actuator.receive()
        sensor.send("POST status=invalid seq=2")
        command = actuator.receive()
        self.assert_all_off(command)
        self.assertEqual(command.sequence, 2)

    def test_missing_registration_and_wrong_role(self):
        peer = self.peer()
        peer.send("POST distance=10")
        self.assertEqual(peer.receive().args["code"], "REGISTER_REQUIRED")
        actuator = self.peer("actuator")
        actuator.send("POST distance=10")
        self.assertEqual(actuator.receive().args["code"], "WRONG_ROLE")

    def test_duplicate_role_does_not_replace_existing_sensor(self):
        sensor = self.peer("sensor")
        duplicate = self.peer()
        duplicate.send("REGISTER type=sensor")
        self.assertEqual(duplicate.receive().args["code"], "ROLE_IN_USE")
        actuator = self.peer("actuator")
        sensor.send("POST distance=10")
        self.assertEqual(actuator.receive().args["redLed"], "blink_4")

    def test_actuator_arrives_after_sensor_without_replaying_old_data(self):
        sensor = self.peer("sensor")
        sensor.send("POST distance=50")
        deadline = time.monotonic() + 1
        while self.server._last_measurement is None and time.monotonic() < deadline:
            time.sleep(0.005)
        actuator = self.peer("actuator")
        sensor.send("POST distance=10")
        self.assertEqual(actuator.receive().args["redLed"], "blink_4")

    def test_measurement_timeout_turns_outputs_off(self):
        actuator = self.peer("actuator")
        sensor = self.peer("sensor")
        sensor.send("POST distance=50")
        self.assertEqual(actuator.receive().args["greenLed"], "on")
        self.assert_all_off(actuator.receive())
        sensor.send("POST distance=30")
        self.assertEqual(actuator.receive().args["yellowLed"], "on")

    def test_sensor_disconnect_and_reconnect(self):
        actuator = self.peer("actuator")
        sensor = self.peer("sensor")
        sensor.send("POST distance=50")
        actuator.receive()
        sensor.close()
        self.assert_all_off(actuator.receive())
        self.wait_unregistered("sensor")
        replacement = self.peer("sensor")
        replacement.send("POST distance=10")
        self.assertEqual(actuator.receive().args["redLed"], "blink_4")

    def test_actuator_reconnect_starts_off_and_waits_for_new_post(self):
        self.peer("sensor")
        actuator = self.peer("actuator")
        actuator.close()
        self.wait_unregistered("actuator")
        self.peer("actuator")

    def test_malformed_message_can_be_followed_by_valid_message(self):
        actuator = self.peer("actuator")
        sensor = self.peer("sensor")
        sensor.send("POST distance=nan")
        self.assertEqual(sensor.receive().args["code"], "BAD_MESSAGE")
        sensor.send("POST distance=30")
        self.assertEqual(actuator.receive().args["yellowLed"], "on")

    def test_oversized_line_closes_connection(self):
        peer = self.peer()
        peer.socket.sendall(b"x" * 257)
        self.assertEqual(peer.receive().args["code"], "LINE_TOO_LONG")
        with self.assertRaises(EOFError):
            peer.receive()

    def test_unregistered_client_timeout(self):
        peer = self.peer()
        self.assertEqual(peer.receive().args["code"], "REGISTER_TIMEOUT")

    def test_port_can_be_reused_after_shutdown(self):
        address = self.server.address
        self.server.stop()
        with TcpServer(ServerConfig(host=address[0], port=address[1])) as replacement:
            self.assertEqual(replacement.address, address)
