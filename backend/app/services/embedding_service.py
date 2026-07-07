import hashlib
import math

EMBEDDING_DIMENSION = 64


def embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSION
    normalized_text = text.lower().strip()
    if not normalized_text:
        return vector

    features: list[str] = []
    for token in normalized_text.split():
        features.append(f"word:{token}")
        if len(token) <= 3:
            features.append(f"ngram:{token}")
        else:
            features.extend(
                f"ngram:{token[index:index + 3]}"
                for index in range(len(token) - 2)
            )

    for feature in features:
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSION
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]
