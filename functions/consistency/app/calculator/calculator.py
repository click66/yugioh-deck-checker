import random
from collections import Counter
from typing import List, Sequence

from app.calculator.exceptions import InvalidCardCountsError
from app.calculator.result import ConsistencyResult


def hand_is_good(hand: Sequence[str], ideal_hands: Sequence[Sequence[str]]) -> bool:
    """Return True if the hand matches any of the ideal hands."""
    hand_counts = Counter(hand)
    return any(
        all(hand_counts[card] >= count for card,
            count in Counter(pattern).items())
        for pattern in ideal_hands
    )


def simple_consistency(
    deckcount: int,
    ratios: Sequence[int],
    names: Sequence[str],
    ideal_hands: Sequence[Sequence[str]],
    num_hands: int = 1_000_000,
) -> ConsistencyResult:
    """Estimate probability that a random 5-card hand matches an ideal hand."""

    # Make local copies to avoid mutating inputs
    ratios = list(ratios)
    names = list(names)

    # Fill deck with 'blank' cards if needed
    blanks = deckcount - sum(ratios)
    if blanks < 0:
        raise InvalidCardCountsError("Ratios add up to more than Deck Count")
    if blanks > 0:
        ratios.append(blanks)
        names.append('blank')

    # Build deck list
    deck: List[str] = [
        card for name, count in zip(names, ratios) for card in [name] * count
    ]

    # Simulate hands
    good_5 = 0
    good_6 = 0

    for _ in range(num_hands):
        shuffled = deck.copy()
        random.shuffle(shuffled)

        hand5 = shuffled[:5]
        if hand_is_good(hand5, ideal_hands):
            good_5 += 1

        hand6 = shuffled[:6]
        if hand_is_good(hand6, ideal_hands):
            good_6 += 1

    return ConsistencyResult(good_5 / num_hands, good_6 / num_hands)
