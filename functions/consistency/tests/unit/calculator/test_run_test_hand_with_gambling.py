import pytest
from app.calculator.calculator import run_test_hand_with_gambling

# Minimal mock card database keyed by card ID
card_database = {
    80181649: {"superType": "spell", "name": "A Case for K9"},
    86988864: {"superType": "monster", "attribute": "EARTH", "race": "Beast", "name": "3-Hump Lacooda"},
    14261867: {"superType": "monster", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
    23771716: {"superType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
    6850209: {"superType": "spell", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},

    # Gamble cards
    1475311: {"superType": "spell", "name": "Allure of Darkness", "race": "Normal"},
}

gambling_cards = {
    1475311: {  # Allure of Darkness
        "draw": 2,
        # must discard one card matching this
        "discard": [("attribute", "DARK")],
    },
    70368879: {  # Upstart Goblin
        "draw": 1,
        "discard": [],
    },
}


def test_exact_match():
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]
    deck = []
    assert run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        deck,
        gambling_cards,
    ) == (True, True)


def test_no_gamble_card_in_hand():
    # 1426187 = 8-Claws Scoropion
    hand = [14261867]

    # 80181649 = A Case for K9
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        remaining_deck,
        gambling_cards,
    )

    # No gamble card in hand, should just fail
    assert result == (False, False)


def test_allure_of_darkness_with_dark():
    # 86988864 = 3-Humped Lacooda
    # 14261867 = 8-Claws Scorpion (Dark Monster)
    # 1475311 = Allure of Darkness
    hand = [86988864, 14261867, 1475311]

    # 80181649 = A Case for K9
    remaining_deck = [80181649, 0]

    # 86988864 = 3-Humped Lacooda
    # 80181649 = A Case for K9
    ideal_hands = [[86988864, 80181649]]

    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        remaining_deck,
        gambling_cards,
    )
    assert result == (False, True)


def test_gamble_without_discardable():
    hand = [1475311]  # Allure of Darkness
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    # There is no DARK card to discard, gamble should not trigger
    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        remaining_deck,
        gambling_cards,
    )
    assert result == (False, False)


def test_discard_constraint_single_count():
    hand = [14261867, 1475311]  # 8-Claws Scorpion is DARK and Insect
    remaining_deck = [80181649]
    gambling_cards_dup = {
        1475311: {
            "draw": 1,
            "discard": [("attribute", "DARK"), ("race", "Insect")]
        }
    }
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        remaining_deck,
        gambling_cards_dup,
    )

    # Only one discardable card exists, gamble should trigger correctly
    assert result == (False, True)


def test_gamble_draw_limited_by_deck():
    hand = [1475311, 14261867]
    remaining_deck = [80181649]  # Only 1 card, but Allure wants to draw 2
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        remaining_deck,
        gambling_cards,
    )

    # Should fail because you cannot Allure with 1 card in deck
    assert result == (False, False)


def test_wildcard_satisfied_by_gamble():
    hand = [1475311, 86988864]  # Allure + Earth Beast
    remaining_deck = [14261867]  # DARK monster
    ideal_hands = [["any_attribute_dark"]]

    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        remaining_deck,
        gambling_cards,
    )

    # Should fail as gambling should not run if the discard requirement
    # is not in the hand to begin with (we may expand on this later)
    assert result == (False, False)
