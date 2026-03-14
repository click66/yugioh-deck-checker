import logging
import random
from collections import Counter
from typing import List, NotRequired, Sequence, TypeAlias, TypedDict, Union

from app.calculator.exceptions import InsufficientDeckSizeError, InvalidCardCountsError
from app.calculator.result import ConsistencyResult


logger = logging.getLogger()
logger.setLevel("INFO")


class Card(TypedDict):
    superType: str
    name: str
    race: NotRequired[str]
    attribute: NotRequired[str]


CardDatabase: TypeAlias = dict[int | str, Card]

DiscardConstraint: TypeAlias = tuple[str, str]


class GambleCard(TypedDict):
    draw: int   # Count of cards this gamble will draw
    discard: NotRequired[list[DiscardConstraint]]


GamblingCards: TypeAlias = dict[int | str, GambleCard]


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
    hand: Sequence[int | str],
    ideal_hands: Sequence[Union[Sequence[str], Counter]],
    card_database: CardDatabase
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


def run_test_hand_with_gambling(
    hand: Sequence[int | str],
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]],
    card_database: dict[int | str, Card],
    remaining_deck: list[int | str],
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
         - Number of times gamlbing cards were seen but the hands did not meet the requirements to play it
    """
    matches_without = hand_is_wild(hand, ideal_hands, card_database)
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
        if card_database.get(int(c), {}).get(field) == value
    ]
    if not discardable:
        return matches_without, matches_with

    # Simulate resolving exactly ONE gamble

    # Remove one copy of gamble from hand (we're activating it)
    new_hand = list(hand)
    new_hand.remove(gamble_card)  # activate the gamble

    # Draw cards
    num_to_draw = spec.get("draw", 0)
    if len(remaining_deck) - num_to_draw:   # Cannot Pot of Greed with 1 card in deck
        return matches_without, matches_with

    drawn_cards = random.sample(remaining_deck, num_to_draw)
    new_hand.extend(drawn_cards)

    # Remove one discardable card (first match)
    for c in new_hand:
        for field, value in discard_requirements:
            info = card_database.get(int(c))
            if info and info.get(field) == value:
                new_hand.remove(c)
                break
        else:
            continue
        break

    # Recheck post-gamble hand
    if hand_is_wild(new_hand, ideal_hands, card_database):
        matches_with = True

    return matches_without, matches_with


def simple_consistency(
    deckcount: int,
    ratios: Sequence[int],
    names: Sequence[int | str],
    ideal_hands: Sequence[Sequence[int | str]],
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
    deckcount = len(deck)

    # Precompute ideal hand counters for efficiency
    ideal_counters: List[Counter] = [
        Counter(pattern) for pattern in ideal_hands
    ]

    good_5 = 0
    good_6 = 0

    for _ in range(num_hands):
        # Draw 5-card hand
        hand5 = random.sample(deck, min(5, deckcount))
        if hand_checker(hand5, ideal_counters):
            good_5 += 1

        # Draw 6-card hand only if deck >= 6
        if deckcount >= 6:
            hand6 = random.sample(deck, 6)
            if hand_checker(hand6, ideal_counters):
                good_6 += 1

    p5 = good_5 / num_hands
    p6 = good_6 / num_hands if len(deck) >= 6 else 0.0

    return ConsistencyResult(p5, p6)
