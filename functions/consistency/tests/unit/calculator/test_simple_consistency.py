import pytest
from app.calculator.calculator import simple_consistency, hand_is_good
from app.calculator.exceptions import InvalidCardCountsError


def hand_checker(_, hand, ideal_hands): return hand_is_good(hand, ideal_hands)


def test_consistency_basic_integer_cards():
    deckcount = 10
    ratios = [2, 3]           # two A Case for K9, three 3-Hump Lacooda
    names = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_checker,
    )
    assert 0.0 <= result.p5 <= 1.0
    assert 0.0 <= result.p6 <= 1.0


def test_consistency_with_blanks_added_integer_cards():
    deckcount = 10
    ratios = [2, 3]  # total 5, 5 blanks added
    names = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_checker,
    )
    assert 0.0 <= result.p5 <= 1.0
    assert 0.0 <= result.p6 <= 1.0


def test_consistency_error_on_overfilled_deck_integer_cards():
    deckcount = 4
    ratios = [2, 3]  # sum = 5 > deckcount
    names = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]

    with pytest.raises(InvalidCardCountsError):
        simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
            ideal_hands=ideal_hands,
            num_hands=10,
            hand_checker=hand_checker,
        )


def test_consistency_full_deck_matches_5_card_hand():
    deckcount = 5
    ratios = [1, 1, 1, 1, 1]
    names = [80181649, 86988864, 14261867, 23771716, 6850209]
    ideal_hands = [[80181649, 86988864, 14261867, 23771716, 6850209]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_checker,
    )
    assert result.p5 == 1.0


def test_consistency_full_deck_matches_6_card_hand():
    deckcount = 6
    ratios = [1, 1, 1, 1, 1, 1]
    names = [80181649, 86988864, 14261867, 23771716, 6850209, 1475311]
    ideal_hands = [[80181649, 86988864, 14261867, 23771716, 6850209, 1475311]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_checker,
    )
    assert result.p6 == 1.0


def test_consistency_hand_never_matches_integer_cards():
    deckcount = 5
    ratios = [5]  # only A Case for K9
    names = [80181649]
    ideal_hands = [[86988864]]  # 3-Hump Lacooda, not in deck

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_checker,
    )
    assert result.p5 == 0.0
    assert result.p6 == 0.0


def test_consistency_does_not_mutate_inputs_integer_cards():
    deckcount = 10
    ratios = [2, 3]
    names = [80181649, 86988864]
    ideal_hands = [[80181649, 86988864]]
    ratios_copy = ratios.copy()
    names_copy = names.copy()

    simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_checker,
    )

    assert ratios == ratios_copy
    assert names == names_copy


def test_consistency_multiple_identical_cards_in_deck():
    deckcount = 6
    ratios = [3, 3]  # three A Case for K9, three 3-Hump Lacooda
    names = [80181649, 86988864]
    # two A Case for K9 and one 3-Hump Lacooda
    ideal_hands = [[80181649, 86988864, 80181649]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=20,
        hand_checker=hand_checker,
    )
    assert result.p5 == 1.0
    assert result.p6 == 1.0
