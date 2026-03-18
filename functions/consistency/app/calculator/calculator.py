from typing import Sequence, TypeAlias
import logging
import random
from collections import Counter
from typing import Callable, Sequence, TypeAlias, TypedDict, Union, NotRequired

from app.calculator.exceptions import InvalidCardCountsError
from app.calculator.result import ConsistencyResult, HandTestResult

logger = logging.getLogger()
logger.setLevel("INFO")

CardID: TypeAlias = int
AttrKey: TypeAlias = tuple[str, str]
ExactPattern: TypeAlias = dict[CardID, int]
WildPattern: TypeAlias = dict[AttrKey, int]
CompiledPattern: TypeAlias = tuple[ExactPattern, WildPattern]
CardAttrIndex: TypeAlias = dict[CardID, dict[AttrKey, int]]


class Card(TypedDict):
    superType: str
    name: str
    race: NotRequired[str]
    attribute: NotRequired[str]


CardDatabase: TypeAlias = dict[CardID, Card]
DiscardConstraint: TypeAlias = tuple[str, str]


class GambleCard(TypedDict):
    draw: int
    discard: NotRequired[list[DiscardConstraint]]


GamblingCards: TypeAlias = dict[CardID, GambleCard]


def hand_is_good(
    hand: Sequence[int],
    ideal_hands: Sequence[Union[Sequence[int | str], Counter]]
) -> bool:
    """
    Simple checking from original code, no longer called.
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
    hand: Sequence[CardID],
    compiled_patterns: list[CompiledPattern],
    card_attr_index: CardAttrIndex,
) -> int:
    """
    Return the number of compiled patterns matched by the hand.
    """
    hand_counter = {}
    for c in hand:
        hand_counter[c] = hand_counter.get(c, 0) + 1

    attr_counter = {}
    for card in hand:
        card_attrs = card_attr_index.get(card)
        if card_attrs:
            for attr, val in card_attrs.items():
                attr_counter[attr] = attr_counter.get(attr, 0) + val

    hand_get = hand_counter.get
    attr_get = attr_counter.get
    card_attr_get = card_attr_index.get

    matched_count = 0

    for exact, wild in compiled_patterns:
        remaining_attrs = {}
        for card, count in exact.items():
            if hand_get(card, 0) < count:
                break
            card_attrs = card_attr_get(card)
            if card_attrs:
                for attr, val in card_attrs.items():
                    remaining_attrs[attr] = remaining_attrs.get(
                        attr, 0) - val * count
        else:
            for attr, count in wild.items():
                available = attr_get(attr, 0) + remaining_attrs.get(attr, 0)
                if available < count:
                    break
            else:
                matched_count += 1

    return matched_count


def run_test_hand_without_gambling(
    hand_checker: callable,
    hand: Sequence[int],
) -> HandTestResult:
    result = hand_checker(hand)
    return HandTestResult(
        matches_without_gambling=result,
        matches_with_gambling=result,
        rescued_with_gambling=0,
        useful_gambles=Counter(),
        gamble_seen=Counter(),
        gamble_attempted=0,
        gamble_failed=0,
        gamble_unplayable=0,
    )


def run_test_hand_with_gambling(
    hand_checker: callable,
    hand: Sequence[int],
    card_attr_index: CardAttrIndex,
    remaining_deck: list[int],
    gambling_cards: GamblingCards,
) -> HandTestResult:

    matches_without = hand_checker(hand)
    matches_with = matches_without
    rescued_with_gambling = 0

    useful_gambles: Counter[int] = Counter()
    gamble_seen: Counter[int] = Counter()
    gamble_attempted = 0
    gamble_failed = 0
    gamble_unplayable = 0

    if matches_without:
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

    gamble_seen[gamble_card] += 1
    spec = gambling_cards[gamble_card]
    discard_requirements = spec.get("discard", [])

    if discard_requirements:
        discardable = [
            c for c in hand
            for field, value in discard_requirements
            if card_attr_index.get(c, {}).get((field, value), 0) > 0
        ]
        if not discardable:
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
    else:
        discardable = []

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

    for c in new_hand:
        for field, value in discard_requirements:
            if card_attr_index.get(c, {}).get((field, value), 0) > 0:
                new_hand.remove(c)
                break
        else:
            continue
        break

    if hand_checker(new_hand):
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


def simple_consistency(
    deckcount: int,
    ratios: Sequence[int],
    names: Sequence[int],
    hand_tester: Callable,  # Returns HandTestResult
    num_hands: int = 1_000_000,
) -> ConsistencyResult:
    ratios = ratios.copy()
    names = names.copy()

    blanks = deckcount - sum(ratios)
    if blanks < 0:
        raise InvalidCardCountsError("Ratios add up to more than deck count")
    if blanks > 0:
        ratios.append(blanks)
        names.append(0)

    deck: list[int] = [int(card) for name, count in zip(
        names, ratios) for card in [name] * count]
    deckcount = len(deck)

    good_5 = good_6 = rescued_5 = rescued_6 = 0
    failed_gambles_5 = failed_gambles_6 = 0
    unplayable_gambles_5 = unplayable_gambles_6 = 0
    gamble_attempted_5 = gamble_attempted_6 = 0
    gamble_seen_5: Counter[int] = Counter()
    gamble_seen_6: Counter[int] = Counter()
    useful_gambles_5: Counter[int] = Counter()
    useful_gambles_6: Counter[int] = Counter()

    # New actionable metrics
    near_miss_counts: Counter[int] = Counter()
    blocking_card_counts: Counter[int] = Counter()
    ideal_hand_counts: Counter[int] = Counter()

    # Track per-hand matched patterns (raw counts)
    matched_pattern_counts_5: Counter[int] = Counter()
    matched_pattern_counts_6: Counter[int] = Counter()
    matched_pattern_counts_5_withgamble: Counter[int] = Counter()
    matched_pattern_counts_6_withgamble: Counter[int] = Counter()

    for _ in range(num_hands):
        hand5 = random.sample(deck, min(5, deckcount))
        remaining_deck_5 = deck.copy()
        for card in hand5:
            remaining_deck_5.remove(card)

        result5: HandTestResult = hand_tester(remaining_deck_5, hand5.copy())

        # Raw counts for pattern matches
        matched_pattern_counts_5[result5.matches_without_gambling] += 1
        total_matches_5 = result5.matches_without_gambling + result5.rescued_with_gambling
        matched_pattern_counts_5_withgamble[total_matches_5] += 1

        if result5.matches_without_gambling > 0:
            good_5 += 1
            for c in hand5:
                ideal_hand_counts[c] += 1
        else:
            for c in hand5:
                blocking_card_counts[c] += 1
            for c in set(deck) - set(hand5):
                near_miss_counts[c] += 1

        rescued_5 += result5.rescued_with_gambling
        failed_gambles_5 += result5.gamble_failed
        unplayable_gambles_5 += result5.gamble_unplayable
        gamble_attempted_5 += result5.gamble_attempted
        gamble_seen_5.update(result5.gamble_seen)
        useful_gambles_5.update(result5.useful_gambles)

        if deckcount >= 6:
            remaining_deck_for_6 = remaining_deck_5.copy()
            extra_card = random.choice(remaining_deck_for_6)
            hand6 = hand5 + [extra_card]
            remaining_deck_for_6.remove(extra_card)

            result6: HandTestResult = hand_tester(remaining_deck_for_6, hand6)

            matched_pattern_counts_6[result6.matches_without_gambling] += 1
            total_matches_6 = result6.matches_without_gambling + result6.rescued_with_gambling
            matched_pattern_counts_6_withgamble[total_matches_6] += 1

            if result6.matches_without_gambling > 0:
                good_6 += 1
                for c in hand6:
                    ideal_hand_counts[c] += 1
            else:
                for c in hand6:
                    blocking_card_counts[c] += 1
                for c in set(deck) - set(hand6):
                    near_miss_counts[c] += 1

            rescued_6 += result6.rescued_with_gambling
            failed_gambles_6 += result6.gamble_failed
            unplayable_gambles_6 += result6.gamble_unplayable
            gamble_attempted_6 += result6.gamble_attempted
            gamble_seen_6.update(result6.gamble_seen)
            useful_gambles_6.update(result6.useful_gambles)

    p5 = good_5 / num_hands
    p6 = good_6 / num_hands if deckcount >= 6 else 0.0
    p5_with_gambling = (good_5 + rescued_5) / num_hands
    p6_with_gambling = (good_6 + rescued_6) / \
        num_hands if deckcount >= 6 else 0.0

    return ConsistencyResult(
        num_hands=num_hands,
        p5=p5,
        p6=p6,
        p5_with_gambling=p5_with_gambling,
        p6_with_gambling=p6_with_gambling,
        rescued_5=rescued_5,
        rescued_6=rescued_6,
        useful_gambles_5=useful_gambles_5,
        useful_gambles_6=useful_gambles_6,
        gamble_seen_5=gamble_seen_5,
        gamble_seen_6=gamble_seen_6,
        gamble_attempted_5=gamble_attempted_5,
        gamble_attempted_6=gamble_attempted_6,
        failed_gambles_5=failed_gambles_5,
        failed_gambles_6=failed_gambles_6,
        unplayable_gambles_5=unplayable_gambles_5,
        unplayable_gambles_6=unplayable_gambles_6,
        near_miss_counts=near_miss_counts,
        blocking_card_counts=blocking_card_counts,
        ideal_hand_counts=ideal_hand_counts,
        matched_pattern_counts_5=matched_pattern_counts_5,
        matched_pattern_counts_6=matched_pattern_counts_6,
        matched_pattern_counts_5_withgamble=matched_pattern_counts_5_withgamble,
        matched_pattern_counts_6_withgamble=matched_pattern_counts_6_withgamble,
    )
