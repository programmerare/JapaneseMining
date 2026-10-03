from dataclasses import dataclass


@dataclass
class HeatmapData:
    """Learned/remaining kanji broken out for the progress heatmap."""

    learned: list[str]
    remaining: list[str]
    learned_count: int
    total_count: int
    keywords: dict[str, str]
    knowledge: dict[str, float]
