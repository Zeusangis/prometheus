from dataclasses import dataclass, field
from math import log1p

from services.calibration_engine import CalibrationEngine
from services.repo_feature_extractor import SkillEvidence


@dataclass
class SkillScoreResult:
    score: int = 0
    confidence: int = 0
    repos: int = 0
    evidence: list[str] = field(default_factory=list)
    stabilized_score: float = 0.0


class SkillScorer:
    def __init__(self, calibration_engine: CalibrationEngine | None = None):
        self.calibration = calibration_engine or CalibrationEngine()
        self.signal_weights = {
            "keyword": 0.18,
            "language": 0.22,
            "topic": 0.18,
            "embedding": 0.26,
            "structure": 0.10,
            "quality": 0.06,
        }

    def score_skill(
        self,
        evidence_list: list[SkillEvidence],
        uncertainty_multiplier: float = 1.0,
    ) -> SkillScoreResult:
        if not evidence_list:
            return SkillScoreResult()

        raw_signal = 0.0
        total_possible = 0.0
        ranking_items = []

        for evidence in evidence_list:
            per_repo_signal = (
                self.signal_weights["keyword"] * evidence.keyword_score
                + self.signal_weights["language"] * evidence.language_score
                + self.signal_weights["topic"] * evidence.topic_score
                + self.signal_weights["embedding"] * evidence.embedding_score
                + self.signal_weights["structure"] * evidence.repo_structure_score
                + self.signal_weights["quality"] * evidence.repo_quality_score
            )
            repo_weight = max(0.4, min(evidence.repo_importance, 1.4))
            capped_signal = min(per_repo_signal, 1.0)

            raw_signal += capped_signal * repo_weight
            total_possible += 1.0 * repo_weight
            ranking_items.append((capped_signal * repo_weight, evidence.repo_name))

        evidence_count = len(evidence_list)
        stabilized = self.calibration.stabilize(
            raw_signal, total_possible, evidence_count
        )
        score = self.calibration.calibrate_score(stabilized)

        evidence_strength_factor = min(log1p(evidence_count) / log1p(6), 1.0)
        confidence = self.calibration.calibrate_confidence(
            calibrated_score=score,
            uncertainty_multiplier=max(0.55, min(uncertainty_multiplier, 1.0)),
            evidence_strength_factor=evidence_strength_factor,
        )

        ranking_items.sort(key=lambda item: item[0], reverse=True)
        top_evidence = [name for _, name in ranking_items[:5]]

        return SkillScoreResult(
            score=score,
            confidence=confidence,
            repos=evidence_count,
            evidence=top_evidence,
            stabilized_score=stabilized,
        )
