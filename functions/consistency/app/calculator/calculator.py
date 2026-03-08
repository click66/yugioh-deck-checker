import random
from collections import Counter
from typing import Any, Callable, Dict, List, Sequence, Union

from app.calculator.exceptions import InvalidCardCountsError
from app.calculator.result import ConsistencyResult


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
    hand: Sequence[int],
    ideal_hands: Sequence[Union[Sequence[Union[int, str, Callable[[int], bool]]], Counter]],
    wildcard_lookup: Dict[str, Callable[[int], bool]],
) -> bool:
    """
    Return True if the hand matches any ideal hand.
    Supports:
      - exact card IDs (int)
      - wildcard strings (via wildcard_lookup)
      - callable predicates
    Accepts Counters containing exact IDs and wildcards.
    """

    hand_counter = Counter(hand)

    # Preprocess patterns
    processed_patterns: List[Dict[str, Any]] = []

    for pattern in ideal_hands:
        if isinstance(pattern, Counter):
            items = list(pattern.items())
        else:
            # Convert list pattern to (item, count) pairs
            c = Counter(pattern)
            items = list(c.items())

        exact_counter = Counter()
        wildcards: List[Union[str, Callable]] = []

        for key, count in items:
            if isinstance(key, int):
                exact_counter[key] += count
            elif isinstance(key, str):
                # wildcard string repeated 'count' times
                wildcards.extend([key] * count)
            elif callable(key):
                wildcards.extend([key] * count)
            else:
                raise TypeError(f"Unsupported pattern type: {type(key)}")

        processed_patterns.append(
            {"counter": exact_counter,
             "wildcards": wildcards,
             })

    # Match patterns
    for pat in processed_patterns:
        remaining = hand_counter.copy()

        # Match exact IDs first
        exact_counter: Counter = pat["counter"]
        for card_id, count in exact_counter.items():
            if remaining[card_id] < count:
                break
            remaining[card_id] -= count
        else:
            # Match wildcards / callable predicates
            for target in pat["wildcards"]:
                found = False
                for card_id in remaining:
                    if remaining[card_id] <= 0:
                        continue
                    if isinstance(target, str):
                        predicate = wildcard_lookup.get(target)
                        if predicate is None:
                            raise ValueError(f"Unknown wildcard: {target}")
                        if predicate(card_id):
                            remaining[card_id] -= 1
                            found = True
                            break
                    elif callable(target):
                        if target(card_id):
                            remaining[card_id] -= 1
                            found = True
                            break
                if not found:
                    break  # This pattern fails
            else:
                return True  # All wildcards matched

    return False


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
