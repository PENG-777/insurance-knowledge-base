import hashlib
import re

import numpy as np

PUNCT_RE = re.compile(r"[\s，。、；：！？（）()\[\]【】《》\"'“”‘’·\-—…,.;:!?/\\|]+")


class HashingEmbedder:
    """字符 2/3-gram 哈希向量器：512 维、L2 归一化，无需外部模型。"""

    dim = 512

    def _clean(self, text: str) -> str:
        return PUNCT_RE.sub("", (text or "").lower())

    def encode(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        cleaned = self._clean(text)
        if not cleaned:
            return vec.tolist()
        for n, weight in ((2, 1.0), (3, 1.3)):
            if len(cleaned) < n:
                continue
            for i in range(len(cleaned) - n + 1):
                gram = cleaned[i : i + n]
                digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
                idx = int.from_bytes(digest, "big") % self.dim
                vec[idx] += weight
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec.astype(float).tolist()


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def bigram_set(text: str) -> set[str]:
    cleaned = PUNCT_RE.sub("", text or "")
    if len(cleaned) < 2:
        return set(cleaned)
    return {cleaned[i : i + 2] for i in range(len(cleaned) - 1)}
