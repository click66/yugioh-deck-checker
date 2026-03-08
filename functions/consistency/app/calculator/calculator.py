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

    def match_pattern(pattern: Union[Sequence[Union[int, str]], Counter]) -> bool:
        pat_counter = pattern if isinstance(
            pattern, Counter) else Counter(pattern)

        # Track remaining wildcard counts
        remaining_types = {}

        # First subtract exact cards from hand_counter
        for card, count in pat_counter.items():
            if not (isinstance(card, str) and card.startswith("any_")):
                card_info = card_database.get(int(card))
                if card_info is None:
                    # exact card missing -> pattern cannot match
                    return False
                # Decrement remaining count of this card type for potential wildcard
                remaining_types.setdefault(card_info["frameType"], 0)
                remaining_types[card_info["frameType"]] -= count
                if hand_counter[card] < count:
                    return False

        # Now check wildcards
        for card, count in pat_counter.items():
            if isinstance(card, str) and card.startswith("any_"):
                logger.info(
                    'Detected wildcard %s in pattern %s for hand %s',
                    card,
                    pat_counter,
                    hand
                )
                type_name = card[4:]
                # Count cards of this type in hand (excluding exact matches already subtracted)
                
                hand_types = [card_database.get(int(c), {}).get("frameType") == type_name for c in 
                hand]
                logger.info('Determined hand card types %s', hand_types)

                type_count = sum(
                    1
                    for c in hand
                    if card_database.get(int(c), {}).get("frameType") == type_name
                )
                # subtract exact cards
                type_count += remaining_types.get(type_name, 0)
                if type_count < count:
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
