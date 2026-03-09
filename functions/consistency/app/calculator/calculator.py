import logging
import random
from collections import Counter
from typing import List, Sequence, Union

from app.calculator.exceptions import InvalidCardCountsError
from app.calculator.result import ConsistencyResult


logger = logging.getLogger()
logger.setLevel("INFO")


def hand_is_good(
    hand: Sequence[str],
    ideal_hands: Sequence[Union[Sequence[str], Counter]]
) -> bool:
    """
    Return True if the hand matches any of the ideal hands.
    Accepts ideal_hands as list of lists (for tests) or list of Counters (optimized).
    """
    hand_counter = Counter(hand)

    # Convert ideal_hands to counters if not already
    ideal_counters = [
        pattern if isinstance(pattern, Counter) else Counter(pattern)
        for pattern in ideal_hands
    ]

    return any(
        all(hand_counter[card] >= count for card, count in pattern.items())
        for pattern in ideal_counters
    )


def hand_is_wild(
    hand: Sequence[str],
    ideal_hands: Sequence[Union[Sequence[str], Counter]],
    card_database: dict
) -> bool:
    """
    Return True if the hand matches any of the ideal hands.
    Supports wildcards like:
        any_superType_monster
        any_attribute_dark
        any_race_quick-play
    Accepts ideal_hands as list of lists (for tests) or list of Counters (optimized).
    """

    hand_counter = Counter(hand)

    # Precompute attribute counts for the hand (all fields)
    attr_counter = Counter()
    for c in hand:
        info = card_database.get(int(c))
        if info:
            for field, value in info.items():
                if value is not None:
                    attr_counter[(field, value)] += 1

    def match_pattern(pattern: Union[Sequence[Union[int, str]], Counter]) -> bool:
        pat_counter = pattern if isinstance(
            pattern, Counter) else Counter(pattern)

        remaining_attrs = Counter()

        # First check exact cards
        for card, count in pat_counter.items():
            if not (isinstance(card, str) and card.startswith("any_")):
                card_info = card_database.get(int(card))
                if card_info is None:
                    return False

                if hand_counter[card] < count:
                    return False

                for field, value in card_info.items():
                    if value is not None:
                        remaining_attrs[(field, value)] -= count

        # Now check wildcards
        for card, count in pat_counter.items():
            if isinstance(card, str) and card.startswith("any_"):
                # Wildcard format: any_<field>_<value>
                _, field, value = card.split("_", 2)

                available = attr_counter.get(
                    (field, value), 0) + remaining_attrs.get((field, value), 0)

                if available < count:
                    return False

        return True

    return any(match_pattern(pattern) for pattern in ideal_hands)


def simple_consistency(
    deckcount: int,
    ratios: Sequence[int],
    names: Sequence[str],
    ideal_hands: Sequence[Sequence[str]],
    hand_checker: callable,
    num_hands: int = 1_000_000,
) -> ConsistencyResult:
    """Estimate probability that a random 5-card (and 6-card) hand matches an ideal hand."""

    # Make local copies to avoid mutation of originals
    ratios = ratios.copy()
    names = names.copy()

    # Validate size & fill deck to deck count with blanks
    blanks = deckcount - sum(ratios)
    if blanks < 0:
        raise InvalidCardCountsError("Ratios add up to more than Deck Count")
    if blanks > 0:
        ratios.append(blanks)
        names.append(00000000)

    # Build deck
    deck: List[str] = [
        card for name, count in zip(names, ratios) for card in [name] * count
    ]

    # Precompute ideal hand counters for efficiency
    ideal_counters: List[Counter] = [
        Counter(pattern) for pattern in ideal_hands
    ]

    good_5 = 0
    good_6 = 0

    for _ in range(num_hands):
        # Draw 5-card hand
        hand5 = random.sample(deck, 5)
        if hand_checker(hand5, ideal_counters):
            good_5 += 1

        # Draw 6-card hand only if deck >= 6
        if len(deck) >= 6:
            hand6 = random.sample(deck, 6)
            if hand_checker(hand6, ideal_counters):
                good_6 += 1

    p5 = good_5 / num_hands
    p6 = good_6 / num_hands if len(deck) >= 6 else 0.0

    return ConsistencyResult(p5, p6)
