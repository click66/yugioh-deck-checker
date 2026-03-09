from app.calculator.calculator import run_test_hand_with_gambling

# Minimal mock card database keyed by card ID
card_database = {
    80181649: {"superType": "spell", "name": "A Case for K9"},
    86988864: {"superType": "monster", "race": "Beast", "name": "3-Hump Lacooda"},
    14261867: {"superType": "monster", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
    23771716: {"superType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
    6850209: {"superType": "spell", "attribute": "DARK", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},
    86988864: {"superType": "trap", "name": "A Feint Plan"},

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


def test_allure_of_darkness_with_dark():
    # 86988864 = A Feint Plan
    # 14261867 = 8-Claws Scorpion (Dark Monster)
    # 1475311 = Allure of Darkness
    hand = [86988864, 14261867, 1475311]

    # 80181649 = A Case for K9
    deck = [86988864, 14261867, 1475311, 80181649, 0]

    # 86988864 = A Feint Plan
    # 80181649 = A Case for K9
    ideal_hands = [[86988864, 80181649]]

    result = run_test_hand_with_gambling(
        hand,
        ideal_hands,
        card_database,
        deck,
        gambling_cards,
    )
    assert result == (False, True)
