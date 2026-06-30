from __future__ import annotations


def text_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0
    if len(text_a) < 2 or len(text_b) < 2:
        return 0.0
    bigrams_a = set(zip(text_a, text_a[1:]))
    bigrams_b = set(zip(text_b, text_b[1:]))
    intersection = bigrams_a & bigrams_b
    union = bigrams_a | bigrams_b
    return len(intersection) / len(union) if union else 0.0
