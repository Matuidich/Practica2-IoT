"""Calcula errores por muestra y cadencia a partir de una captura del sensor."""

import argparse
import csv
import json
import math
from pathlib import Path


def analyze(rows: list[dict[str, str]]) -> dict[str, object]:
    if not rows:
        raise ValueError("El archivo no contiene mediciones.")
    timestamps: list[int] = []
    sequences: list[int] = []
    errors: list[float] = []
    valid_count = sent_count = 0
    for row in rows:
        timestamp = int(row["sensor_time_ms"])
        sequence = int(row["seq"])
        valid, sent = int(row["valid"]), int(row["sent"])
        distance = float(row["distance_cm"])
        if not 0 <= timestamp <= 0xFFFFFFFF or not 0 <= sequence <= 0xFFFFFFFF or valid not in (0, 1) or sent not in (0, 1):
            raise ValueError("Timestamp, secuencia o indicadores fuera de rango.")
        if not math.isfinite(distance) or (valid and distance <= 0):
            raise ValueError("Distancia inválida en una lectura marcada como válida.")
        timestamps.append(timestamp)
        sequences.append(sequence)
        valid_count += valid
        sent_count += sent
        if valid and row.get("reference_cm", "") != "":
            reference = float(row["reference_cm"])
            if not math.isfinite(reference) or reference <= 0:
                raise ValueError("Referencia física inválida.")
            errors.append(abs(distance - reference))
    intervals = [(later - earlier) & 0xFFFFFFFF for earlier, later in zip(timestamps, timestamps[1:])]
    sequence_steps = [(later - earlier) & 0xFFFFFFFF for earlier, later in zip(sequences, sequences[1:])]
    if any(interval == 0 or interval > 0x7FFFFFFF for interval in intervals) or any(step == 0 or step > 0x7FFFFFFF for step in sequence_steps):
        raise ValueError("Captura duplicada, desordenada o con reinicio; analizar sesiones separadas.")
    seconds = sum(intervals) / 1000
    rate = None if not intervals else len(intervals) / seconds
    maximum = max(errors) if errors else None
    return {
        "samples": len(rows), "valid_samples": valid_count, "invalid_samples": len(rows) - valid_count,
        "samples_marked_sent": sent_count, "observed_span_s": round(seconds, 3),
        "captured_sample_rate_hz": None if rate is None else round(rate, 3),
        "max_interval_ms": max(intervals) if intervals else None,
        "missing_serial_samples": sum(step - 1 for step in sequence_steps),
        "sampling_at_least_2_hz": None if rate is None else rate >= 2,
        "referenced_samples": len(errors), "max_absolute_error_cm": maximum,
        "referenced_valid_samples_within_3_cm": None if maximum is None else maximum <= 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    try:
        with args.csv_file.open(newline="", encoding="utf-8") as file:
            result = analyze(list(csv.DictReader(file)))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"No se pudo analizar la captura: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
