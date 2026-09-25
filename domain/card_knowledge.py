import math


def get_card_knowledge(self, card) -> float:
    """
    Impure: extracts stability/retrievability from Anki's card stats calling collection_service
    """
    if card.type == 0:
        return 0.0

    stability = retrievability = None
    try:
        stats = self._collection_service.get_card_stats_data_by_card_id(card.id)
        for attr in ("stability", "fsrs_stability", "s"):
            if hasattr(stats, attr) and getattr(stats, attr) is not None:
                stability = float(getattr(stats, attr))
                break
        for attr in ("retrievability", "fsrs_retrievability", "r"):
            if hasattr(stats, attr) and getattr(stats, attr) is not None:
                retrievability = float(getattr(stats, attr))
                break
    except Exception:
        pass

    if stability is None:
        try:
            ms = getattr(card, "memory_state", None)
            if ms is not None and getattr(ms, "stability", None) is not None:
                stability = float(ms.stability)
        except Exception:
            pass

    return _score_knowledge(stability, retrievability)


def _score_knowledge(stability: float | None, retrievability: float | None) -> float:
    """
    Pure: computes a knowledge score based on stability and retrievability.
    """
    if stability is None or stability <= 0:
        return 0.0
    S_MAX = 365.0
    stab_norm = min(1.0, math.log1p(stability) / math.log1p(S_MAX))
    r = 0.9 if retrievability is None else max(0.0, min(1.0, retrievability))
    return max(0.0, min(1.0, 0.75 * stab_norm + 0.25 * r))