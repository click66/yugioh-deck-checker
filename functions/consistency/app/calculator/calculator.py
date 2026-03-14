import logging
import random
from collections import Counter
from typing import Callable, List, Sequence, TypeAlias, TypedDict, Union, NotRequired

from app.calculator.exceptions import InvalidCardCountsError
from app.calculator.result import ConsistencyResult, HandTestResult

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
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]]
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


def run_test_hand_without_gambling(
    hand_checker: callable,
    hand: Sequence[int],
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]],
    card_database: CardDatabase,
) -> HandTestResult:
    result = hand_checker(hand, ideal_hands, card_database)
    return HandTestResult(
        matches_without_gambling=result,
        matches_with_gambling=result,
    )


def run_test_hand_with_gambling(
    hand_checker: callable,
    hand: Sequence[int],
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]],
    card_database: CardDatabase,
    remaining_deck: list[int],
    gambling_cards: GamblingCards,
) -> HandTestResult:
    """
    Run a hand with gambling logic and track detailed metrics:
    - matches_without_gambling: whether hand matches ideal hands without gambling
    - matches_with_gambling: whether hand matches ideal hands after gambling
    - rescued_with_gambling: 1 if gambling rescued the hand, 0 otherwise
    - useful_gambles: Counter of gamble cards that rescued a hand
    - gamble_seen: Counter of gamble cards seen in the hand
    - gamble_attempted: number of gamble cards attempted
    - gamble_failed: number of gambles attempted that did not rescue the hand
    - gamble_unplayable: number of gambles present but could not be played
    """

    matches_without = hand_checker(hand, ideal_hands, card_database)
    matches_with = matches_without

    rescued_with_gambling = 0
    useful_gambles: Counter[int] = Counter()
    gamble_seen: Counter[int] = Counter()
    gamble_attempted = 0
    gamble_failed = 0
    gamble_unplayable = 0

    if matches_without:
        # No gambling needed
        return HandTestResult(
            matches_without_gambling=matches_without,
            matches_with_gambling=matches_with,
            rescued_with_gambling=rescued_with_gambling,
            useful_gambles=useful_gambles,
            gamble_seen=gamble_seen,
            gamble_attempted=gamble_attempted,
            gamble_failed=gamble_failed,
            gamble_unplayable=gamble_unplayable,
        )

    # Try to use gamble only if present
    gamble_card = next((c for c in hand if c in gambling_cards), None)
    if gamble_card is None:
        return HandTestResult(
            matches_without_gambling=matches_without,
            matches_with_gambling=matches_with,
            rescued_with_gambling=rescued_with_gambling,
            useful_gambles=useful_gambles,
            gamble_seen=gamble_seen,
            gamble_attempted=gamble_attempted,
            gamble_failed=gamble_failed,
            gamble_unplayable=gamble_unplayable,
        )

    # Track that we saw the gamble card
    gamble_seen[gamble_card] += 1

    spec = gambling_cards[gamble_card]
    discard_requirements = spec.get("discard", [])

    # Check for discardable cards
    discardable = [
        c for c in hand
        for field, value in discard_requirements
        if card_database.get(c, {}).get(field) == value
    ]
    if discardable is None or not discardable:
        gamble_unplayable += 1
        return HandTestResult(
            matches_without_gambling=matches_without,
            matches_with_gambling=matches_with,
            rescued_with_gambling=rescued_with_gambling,
            useful_gambles=useful_gambles,
            gamble_seen=gamble_seen,
            gamble_attempted=gamble_attempted,
            gamble_failed=gamble_failed,
            gamble_unplayable=gamble_unplayable,
        )

    # Simulate resolving exactly ONE gamble
    new_hand = list(hand)
    new_hand.remove(gamble_card)

    num_to_draw = spec.get("draw", 0)
    if len(remaining_deck) < num_to_draw:
        gamble_unplayable += 1
        return HandTestResult(
            matches_without_gambling=matches_without,
            matches_with_gambling=matches_with,
            rescued_with_gambling=rescued_with_gambling,
            useful_gambles=useful_gambles,
            gamble_seen=gamble_seen,
            gamble_attempted=gamble_attempted,
            gamble_failed=gamble_failed,
            gamble_unplayable=gamble_unplayable,
        )

    gamble_attempted += 1

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
        rescued_with_gambling = 1
        useful_gambles[gamble_card] += 1
    else:
        gamble_failed += 1

    return HandTestResult(
        matches_without_gambling=matches_without,
        matches_with_gambling=matches_with,
        rescued_with_gambling=rescued_with_gambling,
        useful_gambles=useful_gambles,
        gamble_seen=gamble_seen,
        gamble_attempted=gamble_attempted,
        gamble_failed=gamble_failed,
        gamble_unplayable=gamble_unplayable,
    )


HandTester = Callable[
    [list[int], Sequence[int], Sequence[Counter]],
    "HandTestResult"
]


def simple_consistency(
    deckcount: int,
    ratios: Sequence[int],
    names: Sequence[int],
    ideal_hands: Sequence[Sequence[int | str]],
    hand_tester: HandTester,
    num_hands: int = 1_000_000,
) -> ConsistencyResult:
    ratios = ratios.copy()
    names = names.copy()

    blanks = deckcount - sum(ratios)
    if blanks < 0:
        raise InvalidCardCountsError("Ratios add up to more than deck count")
    if blanks > 0:
        ratios.append(blanks)
        names.append(0)  # Blank card sentinel

    deck: list[int] = [int(card) for name, count in zip(
        names, ratios) for card in [name] * count]
    deckcount = len(deck)

    def normalize_pattern(pattern):
        return [c if isinstance(c, str) and c.startswith("any_") else int(c) for c in pattern]

    ideal_counters = [Counter(normalize_pattern(p)) for p in ideal_hands]

    # Initialize metrics
    good_5 = good_6 = rescued_5 = rescued_6 = 0
    failed_gambles_5 = failed_gambles_6 = 0
    unplayable_gambles_5 = unplayable_gambles_6 = 0
    gamble_attempted_5 = gamble_attempted_6 = 0
    gamble_seen_5: Counter[int] = Counter()
    gamble_seen_6: Counter[int] = Counter()
    useful_gambles: Counter[int] = Counter()

    for _ in range(num_hands):
        # 5-card hand
        hand5 = random.sample(deck, min(5, deckcount))
        remaining_deck_5 = deck.copy()
        for card in hand5:
            remaining_deck_5.remove(card)

        result5: HandTestResult = hand_tester(
            remaining_deck_5, hand5, ideal_counters)
        if result5.matches_without_gambling:
            good_5 += 1
        if result5.rescued_with_gambling:
            rescued_5 += 1
        failed_gambles_5 += result5.gamble_failed
        unplayable_gambles_5 += result5.gamble_unplayable
        gamble_attempted_5 += result5.gamble_attempted
        gamble_seen_5.update(result5.gamble_seen)
        useful_gambles.update(result5.useful_gambles)

        # 6-card hand
        if deckcount >= 6:
            hand6 = random.sample(deck, 6)
            remaining_deck_6 = deck.copy()
            for card in hand6:
                remaining_deck_6.remove(card)

            result6: HandTestResult = hand_tester(
                remaining_deck_6, hand6, ideal_counters)
            if result6.matches_without_gambling:
                good_6 += 1
            if result6.rescued_with_gambling:
                rescued_6 += 1
            failed_gambles_6 += result6.gamble_failed
            unplayable_gambles_6 += result6.gamble_unplayable
            gamble_attempted_6 += result6.gamble_attempted
            gamble_seen_6.update(result6.gamble_seen)
            useful_gambles.update(result6.useful_gambles)

    p5 = good_5 / num_hands
    p6 = good_6 / num_hands if deckcount >= 6 else 0.0
    p5_with_gambling = (good_5 + rescued_5) / num_hands
    p6_with_gambling = (good_6 + rescued_6) / \
        num_hands if deckcount >= 6 else 0.0

    logger.info("5-card success probability: %.6f (without), %.6f (with), rescued: %d",
                p5, p5_with_gambling, rescued_5)
    logger.info("6-card success probability: %.6f (without), %.6f (with), rescued: %d",
                p6, p6_with_gambling, rescued_6)
    logger.info("Useful gamble cards across all hands: %s", useful_gambles)
    logger.info("Gamble cards seen: 5-card=%s, 6-card=%s",
                gamble_seen_5, gamble_seen_6)
    logger.info("Gamble attempts: 5-card=%d, 6-card=%d",
                gamble_attempted_5, gamble_attempted_6)
    logger.info("Failed gamble attempts: 5-card=%d, 6-card=%d",
                failed_gambles_5, failed_gambles_6)
    logger.info("Unplayable gamble cards: 5-card=%d, 6-card=%d",
                unplayable_gambles_5, unplayable_gambles_6)

    return ConsistencyResult(
        p5=p5,
        p6=p6,
        p5_with_gambling=p5_with_gambling,
        p6_with_gambling=p6_with_gambling,
        rescued_5=rescued_5,
        rescued_6=rescued_6,
        useful_gambles=useful_gambles,
        gamble_seen_5=gamble_seen_5,
        gamble_seen_6=gamble_seen_6,
        gamble_attempted_5=gamble_attempted_5,
        gamble_attempted_6=gamble_attempted_6,
        failed_gambles_5=failed_gambles_5,
        failed_gambles_6=failed_gambles_6,
        unplayable_gambles_5=unplayable_gambles_5,
        unplayable_gambles_6=unplayable_gambles_6
    )
