import pytest
from collections import Counter
from app.calculator.calculator import simple_consistency, hand_is_good
from app.calculator.exceptions import InvalidCardCountsError


def test_consistency_basic_integer_cards():
    deckcount = 10
    ratios = [2, 3]           # two cards of 101, three of 102
    names = [101, 102]
    ideal_hands = [[101, 102]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )
    # Probability must be between 0 and 1
    assert 0.0 <= result.p5 <= 1.0
    assert 0.0 <= result.p6 <= 1.0


def test_consistency_with_blanks_added_integer_cards():
    deckcount = 10
    ratios = [2, 3]           # total 5, so 5 blanks added
    names = [101, 102]
    ideal_hands = [[101, 102]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )
    # Blanks added should not break probability calculation
    assert 0.0 <= result.p5 <= 1.0
    assert 0.0 <= result.p6 <= 1.0


def test_consistency_error_on_overfilled_deck_integer_cards():
    deckcount = 4
    ratios = [2, 3]           # sum = 5 > deckcount
    names = [101, 102]
    ideal_hands = [[101, 102]]

    with pytest.raises(InvalidCardCountsError):
        simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
            ideal_hands=ideal_hands,
            num_hands=10,
            hand_checker=hand_is_good,
        )


def test_consistency_full_deck_matches_5_card_hand():
    deckcount = 5
    ratios = [1, 1, 1, 1, 1]  # one of each card
    names = [101, 102, 103, 104, 105]
    ideal_hands = [[101, 102, 103, 104, 105]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )

    # Full 5-card deck must always match
    assert result.p5 == 1.0


def test_consistency_full_deck_matches_6_card_hand():
    deckcount = 6
    ratios = [1, 1, 1, 1, 1, 1]  # one of each card
    names = [101, 102, 103, 104, 105, 106]
    ideal_hands = [[101, 102, 103, 104, 105, 106]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )

    # Full 6-card deck must always match
    assert result.p6 == 1.0


def test_consistency_hand_never_matches_integer_cards():
    deckcount = 5
    ratios = [5]              # only card 101 present
    names = [101]
    ideal_hands = [[102]]     # no such card in deck

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )
    # Probability must be zero
    assert result.p5 == 0.0
    assert result.p6 == 0.0


def test_consistency_does_not_mutate_inputs_integer_cards():
    deckcount = 10
    ratios = [2, 3]
    names = [101, 102]
    ideal_hands = [[101, 102]]
    ratios_copy = ratios.copy()
    names_copy = names.copy()

    simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )

    assert ratios == ratios_copy
    assert names == names_copy


def test_consistency_multiple_identical_cards_in_deck():
    deckcount = 6
    ratios = [3, 3]           # three of 101, three of 102
    names = [101, 102]
    ideal_hands = [[101, 102, 101]]  # requires two 101s and one 102

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=20,
        hand_checker=hand_is_good,
    )

    # Probability should be >0 but <=1
    assert result.p5 == 1.0
    assert result.p6 == 1.0
