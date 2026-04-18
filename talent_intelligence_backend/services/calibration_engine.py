from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class CalibrationConfig:
    sigmoid_k: float = 10.0
    sigmoid_bias: float = 0.35
    alpha: float = 1.2
    min_evidence_floor: float = 0.05


class CalibrationEngine:
    def __init__(self, config: CalibrationConfig | None = None):
        self.config = config or CalibrationConfig()

    def stabilize(
        self, raw_signal: float, total_possible: float, evidence_count: int
    ) -> float:
        if total_possible <= 0:
            return 0.0

        alpha = self.config.alpha
        stabilized = (raw_signal + alpha) / (total_possible + alpha)

        if evidence_count > 0:
            stabilized = max(stabilized, self.config.min_evidence_floor)

        return max(0.0, min(stabilized, 1.0))

    def calibrate_score(self, stabilized_score: float) -> int:
        x = max(0.0, min(stabilized_score, 1.0))
        k = self.config.sigmoid_k
        bias = self.config.sigmoid_bias
        calibrated = 100.0 / (1.0 + exp(-k * (x - bias)))
        return self.clamp_int(calibrated)

    def calibrate_confidence(
        self,
        calibrated_score: int,
        uncertainty_multiplier: float,
        evidence_strength_factor: float,
    ) -> int:
        base_confidence = calibrated_score / 100.0
        adjusted = base_confidence * uncertainty_multiplier * evidence_strength_factor
        return self.clamp_int(adjusted * 100.0)

    def clamp_int(self, value: float | int) -> int:
        if value != value:  # NaN guard
            return 0
        return max(0, min(100, int(round(float(value)))))
