from dataclasses import dataclass, field
from typing import Counter
from collections import Counter as C


@dataclass
class ConsistencyResult:
    num_hands: int

    # Success probabilities without gambling
    p5: float
    p6: float

    # Success probabilities with gambling applied
    p5_with_gambling: float
    p6_with_gambling: float

    # Map of counts (of matched patterns) to number of hands
    matched_pattern_counts_5: dict[int, float]
    matched_pattern_counts_6: dict[int, float]
    matched_pattern_counts_5_withgamble: dict[int, float]
    matched_pattern_counts_6_withgamble: dict[int, float]

    # Number of hands rescued by gambling
    rescued_5: int
    rescued_6: int

    # Which gambling cards successfully rescued hands
    useful_gambles_5: Counter[int]
    useful_gambles_6: Counter[int]

    # Gamble cards seen in hands
    gamble_seen_5: Counter[int]
    gamble_seen_6: Counter[int]

    # Number of gamble attempts
    gamble_attempted_5: int
    gamble_attempted_6: int

    # Number of failed gamble attempts (attempted but did not rescue)
    failed_gambles_5: int
    failed_gambles_6: int

    # Number of unplayable gambles (present but could not be played)
    unplayable_gambles_5: int
    unplayable_gambles_6: int

    near_miss_counts: Counter[int] = field(default_factory=C)
    blocking_card_counts: Counter[int] = field(default_factory=C)
    ideal_hand_counts: Counter[int] = field(default_factory=C)


@dataclass
class HandTestResult:
    matches_without_gambling: int
    matches_with_gambling: int

    rescued_with_gambling: int = 0

    # gamble cards present in the hand
    gamble_seen: Counter[int] = field(default_factory=Counter)
    # gamble was playable and used
    gamble_attempted: int = 0
    # gamble attempted but did not rescue
    gamble_failed: int = 0
    # gamble card present but requirements not met
    gamble_unplayable: int = 0

    # successful rescues per gamble card
    useful_gambles: Counter[int] = field(default_factory=Counter)
