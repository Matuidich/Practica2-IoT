import unittest

from server.controller import ControlService, DistanceClassifier, DistanceState


class ControllerTests(unittest.TestCase):
    def test_boundaries(self):
        classifier = DistanceClassifier()
        for distance, state in (
            (0.01, DistanceState.NEAR), (19.99, DistanceState.NEAR),
            (20, DistanceState.MID), (20.01, DistanceState.MID),
            (39.99, DistanceState.MID), (40, DistanceState.MID),
            (40.01, DistanceState.FAR), (60, DistanceState.FAR),
        ):
            with self.subTest(distance=distance):
                self.assertEqual(classifier.classify(distance), state)

    def test_invalid_readings_turn_all_leds_off(self):
        for distance in (None, 0, -1, float("nan"), float("inf")):
            with self.subTest(distance=distance):
                command = ControlService().command_for(distance, 43)
                self.assertEqual(command.args, {"redLed": "off", "yellowLed": "off", "greenLed": "off", "seq": "43"})

    def test_each_range_has_one_active_led(self):
        for distance, key, mode in ((10, "redLed", "blink_4"), (30, "yellowLed", "on"), (50, "greenLed", "on")):
            with self.subTest(distance=distance):
                args = ControlService().command_for(distance).args
                self.assertEqual(args[key], mode)
                self.assertEqual(sum(value != "off" for value in args.values()), 1)
