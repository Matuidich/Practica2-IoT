"""Reglas de distancia; no dependen de sockets ni de hardware."""

from enum import Enum
import math

from .protocol import Message


class DistanceState(str, Enum):
    INVALID = "invalid"
    NEAR = "near"
    MID = "mid"
    FAR = "far"


class DistanceClassifier:
    def classify(self, distance: float | None) -> DistanceState:
        if distance is None or not math.isfinite(distance) or distance <= 0:
            return DistanceState.INVALID
        if distance < 20:
            return DistanceState.NEAR
        if distance <= 40:
            return DistanceState.MID
        return DistanceState.FAR


class ControlService:
    def __init__(self) -> None:
        self.classifier = DistanceClassifier()

    def command_for(self, distance: float | None, sequence: int | None = None) -> Message:
        state = self.classifier.classify(distance)
        args = {"redLed": "off", "yellowLed": "off", "greenLed": "off"}
        if state == DistanceState.NEAR:
            args["redLed"] = "blink_4"
        elif state == DistanceState.MID:
            args["yellowLed"] = "on"
        elif state == DistanceState.FAR:
            args["greenLed"] = "on"
        if sequence is not None:
            args["seq"] = str(sequence)
        return Message("SET", args)
