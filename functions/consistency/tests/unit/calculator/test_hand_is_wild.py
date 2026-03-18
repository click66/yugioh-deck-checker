from app.calculator.calculator import hand_is_wild
from app.utils import build_card_attribute_index, compile_patterns

# Minimal mock card database keyed by card ID
CARD_DATABASE = {
    80181649: {"superType": "spell", "name": "A Case for K9"},
    86988864: {"superType": "monster", "race": "Beast", "name": "3-Hump Lacooda"},
    14261867: {"superType": "monster", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
    23771716: {"superType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
    6850209: {"superType": "spell", "attribute": "DARK", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},
    68170903: {"superType": "trap", "name": "A Feint Plan"},
}

CARD_ATTRIBUTE_INDEX = build_card_attribute_index(CARD_DATABASE)


def test_exact_match():
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]
    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1


def test_no_match():
    hand = [80181649, 86988864]
    ideal_hands = [[80181649, 14261867]]
    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 0


def test_wildcard_string_any_superType_spell():
    hand = [80181649, 86988864]  # "3-Hump Lacooda" + "A Case for K9"
    ideal_hands = [[86988864, "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1

    hand2 = [86988864, 68170903]  # "3-Hump Lacooda" + "A Feint Plan"
    assert hand_is_wild(
        hand2,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 0


def test_wildcard_does_not_consider_specifics():
    hand = [80181649, 86988864]  # "A Case for K9" + "3-Hump Lacooda"
    ideal_hands = [[80181649, "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 0


def test_wildcard_considers_duplicates():
    hand = [80181649, 80181649, 86988864]  # "A Case for K9" + "3-Hump Lacooda"
    ideal_hands = [[80181649, "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1


def test_multiple_wildcards():
    hand = [80181649, 80181649, 6850209]
    ideal_hands = [[80181649, "any_superType_spell", "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1


def test_multiple_wildcards_larger_hand():
    hand = [80181649, 6850209]
    ideal_hands = [[80181649, "any_superType_spell", "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 0


def test_multiple_wildcards_larger_hand_duplicates():
    hand = [80181649, 80181649]
    ideal_hands = [[80181649, "any_superType_spell", "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 0


def test_duplicates_in_hand():
    hand = [80181649, 80181649, 86988864]
    ideal_hands = [[80181649, 80181649]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1

    ideal_hands2 = [[80181649, 80181649, 80181649]]
    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands2),
        CARD_ATTRIBUTE_INDEX,
    ) == 0


def test_multiple_ideal_patterns():
    hand = [86988864, 6850209]
    ideal_hands = [[86988864, 80181649], [86988864, "any_superType_spell"]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1


def test_empty_hand_or_empty_ideal():
    hand = []
    ideal_hands = [[]]

    assert hand_is_wild(
        hand,
        compile_patterns(ideal_hands),
        CARD_ATTRIBUTE_INDEX,
    ) == 1

    hand2 = [80181649]
    ideal_hands2 = []

    assert hand_is_wild(
        hand2,
        compile_patterns(ideal_hands2),
        CARD_ATTRIBUTE_INDEX,
    ) == 0
