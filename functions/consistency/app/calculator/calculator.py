import random
from collections import Counter
from typing import List, Sequence

from app.calculator.exceptions import InvalidCardCountsError


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
) -> float:
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
    deck: List[str] = [card for name, count in zip(
        names, ratios) for card in [name] * count]

    # Simulate hands
    good_count = sum(
        1 for _ in range(num_hands)
        if hand_is_good(random.sample(deck, 5), ideal_hands)
    )

    return good_count / num_hands
