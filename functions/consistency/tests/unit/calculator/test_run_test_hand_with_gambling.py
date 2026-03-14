from app.calculator.calculator import hand_is_wild, run_test_hand_with_gambling
from app.calculator.result import HandTestResult

CARD_DATABASE = {
    80181649: {"superType": "spell", "name": "A Case for K9"},
    86988864: {"superType": "monster", "attribute": "EARTH", "race": "Beast", "name": "3-Hump Lacooda"},
    14261867: {"superType": "monster", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
    23771716: {"superType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
    6850209: {"superType": "spell", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},
    1475311: {"superType": "spell", "name": "Allure of Darkness", "race": "Normal"},
}

GAMBLING_CARDS = {
    1475311: {
        "draw": 2,
        "discard": [("attribute", "DARK")],
    },
}


def hand_checker(hand, ideal_hands, card_database) -> HandTestResult:
    return hand_is_wild(hand, ideal_hands, card_database)


def test_exact_match():
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]
    remaining_deck = []
    result = run_test_hand_with_gambling(
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, GAMBLING_CARDS
    )
    assert result.matches_without_gambling is True
    assert result.matches_with_gambling is True


def test_no_gamble_card_in_hand():
    hand = [14261867]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, GAMBLING_CARDS
    )
    assert result.matches_without_gambling is False
    assert result.matches_with_gambling is False


def test_allure_of_darkness_with_dark():
    hand = [86988864, 14261867, 1475311]
    remaining_deck = [80181649, 0]
    ideal_hands = [[86988864, 80181649]]

    result = run_test_hand_with_gambling(
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, GAMBLING_CARDS
    )
    assert result.matches_without_gambling is False
    assert result.matches_with_gambling is True


def test_gamble_without_discardable():
    hand = [1475311]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, GAMBLING_CARDS
    )
    assert result.matches_without_gambling is False
    assert result.matches_with_gambling is False


def test_discard_constraint_single_count():
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
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, gambling_cards_dup
    )
    assert result.matches_without_gambling is False
    assert result.matches_with_gambling is True


def test_gamble_draw_limited_by_deck():
    hand = [1475311, 14261867]
    remaining_deck = [80181649]
    ideal_hands = [[80181649]]

    result = run_test_hand_with_gambling(
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, GAMBLING_CARDS
    )
    assert result.matches_without_gambling is False
    assert result.matches_with_gambling is False


def test_wildcard_satisfied_by_gamble():
    hand = [1475311, 86988864]
    remaining_deck = [14261867]
    ideal_hands = [["any_attribute_dark"]]

    result = run_test_hand_with_gambling(
        hand_checker, hand, ideal_hands, CARD_DATABASE, remaining_deck, GAMBLING_CARDS
    )
    assert result.matches_without_gambling is False
    assert result.matches_with_gambling is False
