from app.calculator.calculator import hand_is_wild

# Minimal mock card database keyed by card ID
card_database = {
    80181649: {"frameType": "spell", "attribute": None, "race": None, "name": "A Case for K9"},
    86988864: {"frameType": "effect", "attribute": None, "race": "Beast", "name": "3-Hump Lacooda"},
    14261867: {"frameType": "effect", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
    23771716: {"frameType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
    6850209: {"frameType": "spell", "attribute": "DARK", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},
    68170903: {"frameType": "trap", "attribute": None, "race": None, "name": "A Feint Plan"},
}

# Wildcard definitions for IDs
wildcard_lookup = {
    "any_spell": lambda card_id: card_database[card_id]["frameType"] == "spell",
    "any_trap": lambda card_id: card_database[card_id]["frameType"] == "trap",
    "any_dark": lambda card_id: card_database[card_id].get("attribute") == "DARK",
}


def test_exact_match():
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]
    assert hand_is_wild(hand, ideal_hands, card_database) is True


def test_no_match():
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 14261867]]
    assert hand_is_wild(hand, ideal_hands, card_database) is False


def test_wildcard_string_any_spell():
    hand = [80181649, 86988864]  # "3-Hump Lacooda" + "A Case for K9"
    ideal_hands = [[86988864, "any_spell"]]

    assert hand_is_wild(hand, ideal_hands, card_database) is True

    hand2 = [86988864, 68170903]  # "3-Hump Lacooda" + "A Feint Plan"
    assert hand_is_wild(hand2, ideal_hands, card_database) is False


def test_wildcard_does_not_consider_specifics():
    hand = [80181649, 86988864]  # "A Case for K9" + "3-Hump Lacooda"
    ideal_hands = [[80181649, "any_spell"]]  # "A Case for K9" + any spell

    assert hand_is_wild(hand, ideal_hands, card_database) is False


def test_wildcard_considers_duplicates():
    hand = [80181649, 80181649, 86988864]  # "A Case for K9" + "3-Hump Lacooda"
    ideal_hands = [[80181649, "any_spell"]]  # "A Case for K9" + any spell

    assert hand_is_wild(hand, ideal_hands, card_database) is True


def test_multiple_wildcards():
    # 80181649 = "A Case for K9" (spell)
    # 6850209  = "A Deal with Dark Ruler" (spell)
    hand = [80181649, 80181649, 6850209]

    # Ideal hand contains multiple wildcards
    ideal_hands = [[80181649, "any_spell", "any_spell"]]

    assert hand_is_wild(hand, ideal_hands, card_database) is True


def test_multiple_wildcards_larger_hand():
    # 80181649 = "A Case for K9" (spell)
    # 6850209  = "A Deal with Dark Ruler" (spell)
    hand = [80181649,  6850209]

    # Ideal hand contains multiple wildcards
    ideal_hands = [[80181649, "any_spell", "any_spell"]]

    assert hand_is_wild(hand, ideal_hands, card_database) is False


def test_multiple_wildcards_larger_hand_duplicates():
    hand = [80181649, 80181649]  # two copies of "A Case for K9", both spells
    ideal_hands = [[80181649, "any_spell", "any_spell"]]

    assert hand_is_wild(hand, ideal_hands, card_database) is False


def test_duplicates_in_hand():
    hand = [80181649, 80181649, 86988864]
    ideal_hands = [[80181649, 80181649]]
    assert hand_is_wild(hand, ideal_hands, card_database) is True

    ideal_hands2 = [[80181649, 80181649, 80181649]]
    assert hand_is_wild(hand, ideal_hands2, card_database) is False


def test_multiple_ideal_patterns():
    hand = [86988864, 6850209]
    ideal_hands = [[86988864, 80181649], [86988864, "any_spell"]]
    assert hand_is_wild(hand, ideal_hands, card_database) is True


def test_empty_hand_or_empty_ideal():
    hand = []
    ideal_hands = [[]]
    assert hand_is_wild(hand, ideal_hands, card_database) is True

    hand2 = [80181649]
    ideal_hands2 = []
    assert hand_is_wild(hand2, ideal_hands2, card_database) is False
