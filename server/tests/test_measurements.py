import unittest

from tools.analyze_measurements import analyze
from tools.capture_serial import parse_sample


class EvidenceToolsTests(unittest.TestCase):
    def rows(self):
        return [dict(seq=str(index + 1), sensor_time_ms=str(index * 250), distance_cm=str(distance),
                     valid="1", sent="1", reference_cm="20") for index, distance in enumerate((20, 21, 24))]

    def test_exactitude_uses_worst_sample_instead_of_average(self):
        result = analyze(self.rows())
        self.assertEqual(result["max_absolute_error_cm"], 4)
        self.assertFalse(result["referenced_valid_samples_within_3_cm"])
        self.assertEqual(result["captured_sample_rate_hz"], 4)

    def test_missing_serial_records_are_reported(self):
        rows = self.rows()
        rows[-1]["seq"] = "4"
        self.assertEqual(analyze(rows)["missing_serial_samples"], 1)

    def test_timer_rollover_is_supported(self):
        rows = self.rows()[:2]
        rows[0]["sensor_time_ms"] = str(2**32 - 100)
        rows[1]["sensor_time_ms"] = "150"
        self.assertEqual(analyze(rows)["captured_sample_rate_hz"], 4)

    def test_reset_requires_separate_sessions(self):
        rows = self.rows()
        rows[-1]["sensor_time_ms"] = "100"
        with self.assertRaises(ValueError):
            analyze(rows)

    def test_empty_data_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            analyze([])

    def test_serial_parser_distinguishes_samples_from_diagnostics(self):
        row = parse_sample("sample seq=4 t_ms=1000 distance_cm=19.80 valid=1 sent=1", 20)
        self.assertEqual(row["reference_cm"], 20)
        self.assertEqual(row["sensor_time_ms"], 1000)
        self.assertIsNone(parse_sample("TCP registered"))
