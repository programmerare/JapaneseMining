from dataclasses import dataclass


@dataclass
class CardObservation:
    """One raw signal about a kanji, taken from a single card/field."""
    kanji: str
    reviewed: bool
    suspended: bool
    knowledge: float
    keyword: str


@dataclass
class KanjiLearningState:
    """Merged learning state for one kanji, across every observation of it."""
    reviewed: bool = False
    suspended: bool = False
    knowledge: float = 0.0
    keyword: str = ""

    @property
    def learned(self) -> bool:
        return self.reviewed or self.suspended


def aggregate_kanji_learning_state(
    observations: list[CardObservation],
) -> dict[str, KanjiLearningState]:
    """
    Merge repeated observations of the same kanji (e.g. seen via both the
    Kanji and Alternative Kanji fields, or on multiple cards) into one
    state per kanji.

    Rules:
    - Any "reviewed" observation wins over a merely "suspended" one.
    - Among reviewed observations, keep the highest knowledge score.
    - A keyword is kept once found; later observations don't overwrite it.
    """
    result: dict[str, KanjiLearningState] = {}
    for obs in observations:
        if not obs.kanji:
            continue
        state = result.setdefault(obs.kanji, KanjiLearningState())
        state.reviewed = state.reviewed or obs.reviewed
        if obs.reviewed:
            state.suspended = False
            if obs.knowledge > state.knowledge:
                state.knowledge = obs.knowledge
        elif obs.suspended and not state.reviewed:
            state.suspended = True
        if obs.keyword and not state.keyword:
            state.keyword = obs.keyword
    return result


def sort_kanji_by_learned_then_alpha(states: dict[str, KanjiLearningState]) -> list[str]:
    """Learned kanji first, then alphabetical within each group (matches original _sort_key)."""
    return sorted(states.keys(), key=lambda k: (not states[k].learned, k))
