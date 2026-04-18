from hashlib import blake2b
from math import sqrt
from typing import Iterable

from services.repo_heuristics import normalize_signal_text

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None


class SkillEmbeddingEngine:
    """
    Embedding abstraction with graceful fallback.

    If sentence-transformers is installed, semantic embeddings are used.
    Otherwise, a deterministic hashed-token vector fallback is used.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None

    def similarity(self, skill_text: str, repo_text: str) -> float:
        if not skill_text.strip() or not repo_text.strip():
            return 0.0

        if self.model is not None:
            vectors = self.model.encode(
                [skill_text, repo_text], normalize_embeddings=True
            )
            score = float(vectors[0] @ vectors[1])
            return max(0.0, min(score, 1.0))

        skill_vec = self._fallback_vectorize(skill_text)
        repo_vec = self._fallback_vectorize(repo_text)
        return self._cosine(skill_vec, repo_vec)

    def skill_prompt(self, skill: str, keywords: Iterable[str]) -> str:
        keyword_text = " ".join(str(k) for k in keywords)
        return f"skill: {skill}. related technologies: {keyword_text}".strip()

    def _fallback_vectorize(self, text: str, dims: int = 128) -> list[float]:
        vec = [0.0] * dims
        normalized = normalize_signal_text(text)
        for token in normalized.split():
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(digest, "big") % dims
            vec[idx] += 1.0

        norm = sqrt(sum(value * value for value in vec))
        if norm == 0:
            return vec
        return [value / norm for value in vec]

    def _cosine(self, vector_a: list[float], vector_b: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = sqrt(sum(a * a for a in vector_a))
        norm_b = sqrt(sum(b * b for b in vector_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(numerator / (norm_a * norm_b), 1.0))
