import logging
import random
from collections import Counter
from typing import List, Sequence, TypeAlias, TypedDict, Union, NotRequired

from app.calculator.exceptions import InvalidCardCountsError
from app.calculator.result import ConsistencyResult

logger = logging.getLogger()
logger.setLevel("INFO")


class Card(TypedDict):
    superType: str
    name: str
    race: NotRequired[str]
    attribute: NotRequired[str]


# Card database keyed by integer card ID
CardDatabase: TypeAlias = dict[int, Card]

# Discard requirements for gamble cards: (field, value)
DiscardConstraint: TypeAlias = tuple[str, str]


class GambleCard(TypedDict):
    draw: int   # Count of cards this gamble will draw
    discard: NotRequired[list[DiscardConstraint]]


# Gambling cards keyed by integer card ID
GamblingCards: TypeAlias = dict[int, GambleCard]


def hand_is_good(
    hand: Sequence[int],
    ideal_hands: Sequence[Union[Sequence[int], Counter]]
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
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]],
    card_database: CardDatabase,
) -> bool:
    """
    Return True if the hand matches any of the ideal hands.
    Rules:
      - Deck contains only ints.
      - Patterns: exact cards are ints, wildcards are strings starting with "any_".
    Logging is included to trace hand, pattern, and matching steps.
    """
    hand_counter = Counter(hand)

    # Precompute attribute counts for the hand
    attr_counter: Counter = Counter()
    for c in hand:
        info = card_database.get(c)
        if info:
            for field, value in info.items():
                if value is not None:
                    attr_counter[(field, value)] += 1

    def match_pattern(pattern: Union[Sequence[int | str], Counter]) -> bool:
        # Convert to Counter if needed
        pat_counter: Counter = pattern if isinstance(
            pattern, Counter) else Counter(pattern)
        remaining_attrs: Counter = Counter()

        logger.info("Comparing hand %s against pattern %s", hand, pat_counter)

        # Check each card in the pattern
        for card, count in pat_counter.items():
            if isinstance(card, str) and card.startswith("any_"):
                # wildcard logic
                _, field, value = card.split("_", 2)
                available = attr_counter.get(
                    (field, value), 0) + remaining_attrs.get((field, value), 0)
                logger.info(
                    "Checking wildcard %s: need %d, available %d", card, count, available)
                if available < count:
                    logger.info("Wildcard %s failed", card)
                    return False
            else:
                # exact-card logic
                card_info = card_database.get(card)
                if card_info is None:
                    logger.info("Exact card %s not in database", card)
                    return False
                if hand_counter.get(card, 0) < count:
                    logger.info(
                        "Hand missing %d of exact card %s", count, card)
                    return False
                # track remaining attributes for wildcards
                for field, value in card_info.items():
                    if value is not None:
                        remaining_attrs[(field, value)] -= count

        logger.info("Pattern matched: %s", pat_counter)
        return True

    # Return True if any pattern matches
    for pattern in ideal_hands:
        if match_pattern(pattern):
            logger.info("Hand %s matches pattern %s", hand, pattern)
            return True

    logger.info("Hand %s did not match any pattern", hand)
    return False


def run_test_hand_with_gambling(
    hand_checker: callable,
    hand: Sequence[int],
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]],
    card_database: CardDatabase,
    remaining_deck: list[int],
    gambling_cards: GamblingCards,
) -> tuple[bool, bool]:
    """
    Run hands with gambling enabled, in addition to basic checking.
    If the given test hand is not one of the ideal hands, but contains
    the ability to gamble, will run the gamble and then re-evaluate the
    hand.

    Arguments:
     - hand: The test hand
     - ideal_hands: Sequence or Counter of ideal hands to check against
     - card_database: Reference to dict of cards
     - deck: Complete deck against which we're testing (test hand will 
        be removed)
     - gambling_cards: Reference to dict of GambleCards

    Will return details of:
     - Count of hands that were ideal without gambling
     - Count of hands that were "rescued" with gambling
     - Most "useful" gambling cards
     - Number of times gambling cards were seen but the hands did not meet the requirements to play it
    """
    matches_without = hand_checker(hand, ideal_hands, card_database)
    matches_with = matches_without

    if matches_without:
        return matches_without, matches_with

    # Try to use gamble only if it can be used "safely"
    gamble_card = next((c for c in hand if c in gambling_cards), None)
    if gamble_card is None:
        return matches_without, matches_with

    spec = gambling_cards[gamble_card]
    discard_requirements = spec.get("discard", [])

    # Need at least 1 discardable card already in hand to avoid punting the whole hand
    discardable = [
        c for c in hand
        for field, value in discard_requirements
        if card_database.get(c, {}).get(field) == value
    ]
    if not discardable:
        return matches_without, matches_with

    # Simulate resolving exactly ONE gamble

    # Remove one copy of gamble from hand (we're activating it)
    new_hand = list(hand)
    new_hand.remove(gamble_card)  # activate the gamble

    # Draw cards
    num_to_draw = spec.get("draw", 0)
    if len(remaining_deck) < num_to_draw:   # Cannot Pot of Greed with insufficient deck
        return matches_without, matches_with

    drawn_cards = random.sample(remaining_deck, num_to_draw)
    new_hand.extend(drawn_cards)

    # Remove one discardable card (first match)
    for c in new_hand:
        for field, value in discard_requirements:
            info = card_database.get(c)
            if info and info.get(field) == value:
                new_hand.remove(c)
                break
        else:
            continue
        break

    # Recheck post-gamble hand
    if hand_checker(new_hand, ideal_hands, card_database):
        matches_with = True

    return matches_without, matches_with


def simple_consistency(
    deckcount: int,
    ratios: Sequence[int],
    names: Sequence[int],
    ideal_hands: Sequence[Sequence[int]],
    hand_checker: callable,
    num_hands: int = 1_000_000,
) -> ConsistencyResult:
    # Make local copies to avoid mutation of originals
    ratios = ratios.copy()
    names = names.copy()

    # Validate size & fill deck to deck count with blanks
    blanks = deckcount - sum(ratios)
    if blanks < 0:
        raise InvalidCardCountsError("Ratios add up to more than deck count")
    if blanks > 0:
        ratios.append(blanks)
        names.append(0)  # Blank card sentinel

    # Build deck
    deck: List[int] = [
        int(card) for name, count in zip(names, ratios) for card in [name] * count
    ]
    deckcount = len(deck)

    logger.info("Fully computed deck: %s", deck)

    # Precompute ideal hand counters for efficiency
    def normalize_pattern(pattern):
        normalized = []
        for c in pattern:
            if isinstance(c, str) and c.startswith("any_"):
                normalized.append(c)
            else:
                normalized.append(int(c))  # force exact cards to int
        return normalized

    ideal_counters = [Counter(normalize_pattern(p)) for p in ideal_hands]

    good_5 = 0
    good_6 = 0

    for i in range(num_hands):
        # Draw 5-card hand
        hand5 = random.sample(deck, min(5, deckcount))
        remaining_deck = deck.copy()
        for card in hand5:
            remaining_deck.remove(card)

        result5 = hand_checker(remaining_deck, hand5, ideal_counters)
        logger.info("5-card hand %d: %s -> %s", i + 1, hand5, result5)
        if result5:
            good_5 += 1

        # Draw 6-card hand only if deck >= 6
        if deckcount >= 6:
            hand6 = random.sample(deck, 6)
            remaining_deck = deck.copy()
            for card in hand6:
                remaining_deck.remove(card)
            result6 = hand_checker(remaining_deck, hand6, ideal_counters)
            logger.info("6-card hand %d: %s -> %s", i + 1, hand6, result6)
            if result6:
                good_6 += 1

    p5 = good_5 / num_hands
    p6 = good_6 / num_hands if deckcount >= 6 else 0.0

    logger.info("5-card success probability: %.6f", p5)
    logger.info("6-card success probability: %.6f", p6)

    return ConsistencyResult(p5, p6)
