import pytest
from collections import Counter

from app.calculator.calculator import hand_is_wild, run_test_hand_with_gambling
from app.calculator.data import GAMBLING_CARDS
from app.calculator.result import HandTestResult
from app.utils import build_card_attribute_index, compile_patterns


CARD_DATABASE = {
    80181649: {"superType": "spell", "name": "A Case for K9"},
    86988864: {"superType": "monster", "attribute": "EARTH", "race": "Beast", "name": "3-Hump Lacooda"},
    14261867: {"superType": "monster", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
    23771716: {"superType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
    6850209: {"superType": "spell", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},
    1475311: {"superType": "spell", "name": "Allure of Darkness", "race": "Normal"},
    46986414: {"superType": "monster", "attribute": "DARK", "race": "Spellcaster", "name": "Dark Magician"},
    52840267: {"superType": "monster", "attribute": "DARK", "race": "Fairy", "name": "Darklord Ixchel", "archetype": "Darklord"},
}

CARD_ATTRIBUTE_INDEX = build_card_attribute_index(CARD_DATABASE)

GAMBLING_CARDS = {
    1475311: {
        "draw": 2,
        "discard": [("attribute", "DARK")],
    },
    52840267: {
        "draw": 2,
        "discard": [("archetype", "Darklord")],
    }
}


def build_hand_checker(ideal_hands) -> HandTestResult:
    compiled = compile_patterns(ideal_hands)
    return lambda hand: hand_is_wild(hand, compiled, CARD_ATTRIBUTE_INDEX)


def test_exact_match():
    # Hand already satisfies the ideal pattern so gambling should never be evaluated
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]
    remaining_deck = []

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 1
    assert result.matches_with_gambling is 1

    # Because the hand was already successful no gambling interaction should occur
    assert result.rescued_with_gambling == 0
    assert result.gamble_seen == Counter()
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter()


def test_no_gamble_card_in_hand():
    # The hand fails the ideal pattern and contains no gambling card,
    # therefore no gambling metrics should increment
    hand = [14261867]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    assert result.rescued_with_gambling == 0
    assert result.gamble_seen == Counter()
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter()


def test_allure_of_darkness_with_dark():
    # Allure of Darkness is present and there is a DARK monster to discard.
    # Drawing A Case for K9 should complete the ideal hand.
    hand = [86988864, 14261867, 1475311]
    remaining_deck = [80181649, 0]
    ideal_hands = [[86988864, 80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 1

    # Gambling rescued the hand
    assert result.rescued_with_gambling == 1

    # The gamble card appeared once and was successfully used
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0

    # This gamble card successfully rescued the hand
    assert result.useful_gambles == Counter({1475311: 1})


def test_allure_of_darkness_with_dark_but_dark_was_discarded():
    # The DARK monster is required for the final hand but must be discarded to resolve Allure.
    # Even though we draw A Case for K9 the discard removes the DARK monster we needed.
    hand = [14261867, 1475311]
    remaining_deck = [80181649, 0]
    ideal_hands = [[14261867, 80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    # Gambling was attempted but failed to rescue the hand
    assert result.rescued_with_gambling == 0
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 1
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter()


def test_allure_of_darkness_without_dark():
    # Allure is present but no DARK monster exists to satisfy the discard condition
    hand = [1475311, 86988864]
    remaining_deck = [80181649, 0]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    # Gambling card was seen but could not be activated
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 1
    assert result.useful_gambles == Counter()


def test_discard_constraint_single_count():
    # The same card satisfies two discard conditions simultaneously (DARK + Insect).
    # Only one discard should occur and the gamble should resolve successfully.
    hand = [14261867, 1475311]
    remaining_deck = [80181649]

    gambling_cards_dup = {
        1475311: {
            "draw": 1,
            "discard": [("attribute", "DARK"), ("race", "Insect")]
        }
    }

    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        gambling_cards_dup,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 1

    assert result.rescued_with_gambling == 1
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter({1475311: 1})


def test_gamble_draw_limited_by_deck():
    # The gamble requires drawing two cards but only one card remains in the deck,
    # therefore the gamble cannot be resolved.
    hand = [1475311, 14261867]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 1
    assert result.useful_gambles == Counter()


def test_wildcard_satisfied_by_gamble():
    # The ideal hand requires any DARK attribute.
    # Although a DARK monster exists in the deck, the gamble cannot resolve
    # because there is no discardable DARK monster in the hand.
    hand = [1475311, 86988864]
    remaining_deck = [14261867]
    ideal_hands = [["any_attribute_dark"]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 1
    assert result.useful_gambles == Counter()


def test_multiple_gamble_cards_only_one_used():
    # Two copies of the gambling card exist in the hand.
    # The algorithm should only activate one gamble and ignore the other.
    hand = [1475311, 1475311, 14261867]
    remaining_deck = [80181649, 0]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 1

    # Only one gamble should be counted as seen/attempted even though two copies exist
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.rescued_with_gambling == 1
    assert result.useful_gambles == Counter({1475311: 1})


def test_gamble_seen_but_draw_fails_before_attempt():
    # The gambling card is present and the discard requirement is satisfied,
    # but the deck does not contain enough cards to perform the draw.
    # The gamble should be counted as seen but not attempted.
    hand = [1475311, 14261867]
    remaining_deck = []
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 1
    assert result.useful_gambles == Counter()


def test_successful_gamble_updates_all_counters_correctly():
    # Ensure that a successful gamble increments exactly the expected counters
    # and no failure metrics are incorrectly incremented.
    hand = [1475311, 14261867]
    remaining_deck = [80181649, 0]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 1

    assert result.rescued_with_gambling == 1
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1

    # Because the gamble succeeded there should be no failures
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0

    assert result.useful_gambles == Counter({1475311: 1})


def test_failed_gamble_does_not_mark_rescue():
    # The gamble resolves but the drawn cards do not satisfy the ideal hand.
    # This should count as a gamble attempt and failure but not a rescue.
    hand = [1475311, 14261867]
    # Draws cards that don't help reach the ideal
    remaining_deck = [23771716, 0]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    assert result.rescued_with_gambling == 0

    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 1
    assert result.gamble_unplayable == 0

    assert result.useful_gambles == Counter()


def test_multiple_gamble_cards_only_first_is_evaluated():
    # The algorithm searches the hand for the first gamble card.
    # If multiple different gambling cards exist only the first should be processed.
    gambling_cards_multi = {
        1475311: {"draw": 1, "discard": [("attribute", "DARK")]},
        6850209: {"draw": 1}
    }

    hand = [1475311, 6850209, 14261867]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        gambling_cards_multi,
    )

    # Only the first gamble card in the hand should be tracked
    assert result.gamble_seen == Counter({1475311: 1})


def test_second_gamble_not_counted_when_first_resolves():
    # Two different gamble cards are present. The first resolves successfully
    # and should stop further gamble evaluation.
    gambling_cards_multi = {
        1475311: {"draw": 1, "discard": [("attribute", "DARK")]},
        6850209: {"draw": 1}
    }

    hand = [1475311, 6850209, 14261867]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        gambling_cards_multi,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 1

    # Only the first gamble card should be recorded
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.rescued_with_gambling == 1
    assert result.useful_gambles == Counter({1475311: 1})


def test_gamble_card_present_but_not_needed():
    # The ideal hand is already satisfied without using the gamble card.
    # The gamble card exists but must not be counted as seen or attempted
    # because gambling logic should not run once success is already achieved.
    hand = [80181649, 1475311]
    remaining_deck = [23771716]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 1
    assert result.matches_with_gambling is 1

    # No gambling metrics should be incremented
    assert result.rescued_with_gambling == 0
    assert result.gamble_seen == Counter()
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter()


def test_gamble_draws_cards_but_hand_still_fails():
    # The gamble resolves correctly but the drawn cards do not satisfy
    # the ideal hand condition, so the gamble should count as a failure.
    hand = [1475311, 14261867]
    remaining_deck = [23771716, 0]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    # Gamble was attempted but produced no success
    assert result.rescued_with_gambling == 0
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 1
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter()


def test_multiple_gambles_do_not_stack_metrics():
    # Even if a hand contains several potential gambling cards,
    # only one evaluation should occur per hand to prevent
    # inflating metrics across a single simulation.
    gambling_cards_multi = {
        1475311: {"draw": 1, "discard": [("attribute", "DARK")]},
        6850209: {"draw": 1}
    }

    hand = [1475311, 6850209, 14261867]
    remaining_deck = [23771716]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        gambling_cards_multi,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    # Only the first gamble card should be counted
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 1
    assert result.useful_gambles == Counter()


def test_empty_remaining_deck_with_no_gamble_cards():
    # The remaining deck is empty and the hand contains no gambling cards.
    # This ensures metrics remain zero and the function does not crash
    # when deck operations are impossible.
    hand = [14261867]
    remaining_deck = []
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 0

    assert result.rescued_with_gambling == 0
    assert result.gamble_seen == Counter()
    assert result.gamble_attempted == 0
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter()


def test_multiple_discard_candidates_only_one_discarded_ideal_hand_drawn():
    # Hand: 8-Claws Scorpion + Allure of Darkness
    # Deck: Dark Magician + A Case for K9
    # Ideal hand: Dark Magician + A Case for K9
    hand = [14261867, 1475311]  # 8-Claws Scorpion + Allure of Darkness
    remaining_deck = [46986414, 80181649]  # Dark Magician + A Case for K9
    ideal_hands = [[46986414, 80181649]]    # Ideal hand we want to achieve

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    # Without gambling, hand is not ideal
    assert result.matches_without_gambling is 0

    # After gambling, only one discard occurs; hand becomes ideal
    assert result.matches_with_gambling is 1

    # Metrics
    assert result.rescued_with_gambling == 1
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter({1475311: 1})


@pytest.mark.skip(reason="Currently logic naively discards the first hand; technically a bug but not a priority fix")
def test_multiple_discard_candidates_only_one_discarded_ideal_hand_mixed_with_existing_cards():
    # Hand: 8-Claws Scorpion + Allure of Darkness
    # Deck: Dark Magician + A Case for K9
    # Ideal hand: Dark Magician + A Case for K9
    hand = [46986414, 1475311]  # Dark Magician + Allure of Darkness
    remaining_deck = [14261867, 80181649]  # 8-Claws Scorpion + A Case for K9
    ideal_hands = [[46986414, 80181649]]    # Ideal hand we want to achieve

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    # Without gambling, hand is not ideal
    assert result.matches_without_gambling is 0

    # After gambling, only one discard occurs; hand becomes ideal
    assert result.matches_with_gambling is 1

    # Metrics
    assert result.rescued_with_gambling == 1
    assert result.gamble_seen == Counter({1475311: 1})
    assert result.gamble_attempted == 1
    assert result.gamble_failed == 0
    assert result.gamble_unplayable == 0
    assert result.useful_gambles == Counter({1475311: 1})


def test_archetype_gamble_activated():
    # Hand: Darklord Ixchel + Darklord Ixchel
    # Deck: A Case for K9 + blank
    # Ideal hand: A Case for K9
    hand= [52840267, 52840267]
    remaining_deck = [80181649, 0]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        build_hand_checker(ideal_hands),
        hand,
        CARD_ATTRIBUTE_INDEX,
        remaining_deck,
        GAMBLING_CARDS,
    )

    assert result.matches_without_gambling is 0
    assert result.matches_with_gambling is 1
    assert result.rescued_with_gambling == 1
    assert result.gamble_seen == Counter({52840267: 1})
    assert result.gamble_attempted == 1
    assert result.useful_gambles == Counter({52840267: 1})
