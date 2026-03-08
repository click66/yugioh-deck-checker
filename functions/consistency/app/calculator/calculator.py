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
    Supports wildcards like "any_spell".
    Accepts ideal_hands as list of lists (for tests) or list of Counters (optimized).
    """
    hand_counter = Counter(hand)

    # Precompute counts for hand by card type for wildcard matching
    type_counts = {
        "spell": sum(1 for card in hand if card_database[int(card)]["frameType"] == "spell"),
        "trap": sum(1 for card in hand if card_database[int(card)]["frameType"] == "trap"),
        "effect": sum(1 for card in hand if card_database[int(card)]["frameType"] == "effect"),
        # Add more wildcard types if needed
    }

    def match_pattern(pattern: Union[Sequence[Union[int, str]], Counter]) -> bool:
        # Convert to counter if not already
        pat_counter = pattern if isinstance(
            pattern,
            Counter,
        ) else Counter(pattern)

        remaining_types = type_counts.copy()
        for card, count in pat_counter.items():
            if isinstance(card, str) and card.startswith("any_"):
                logger.info(
                    'Detected wildcard %s in pattern %s for hand %s',
                    card,
                    pat_counter,
                    hand
                )
                # Wildcard: "any_spell" -> "spell"
                type_name = card[4:]
                if remaining_types.get(type_name, 0) < count:
                    return False
                remaining_types[type_name] -= count
            else:
                if hand_counter[card] < count:
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
        names.append("blank")

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
