import pytest
from app.calculator.calculator import simple_consistency, hand_is_good
from app.calculator.exceptions import InvalidCardCountsError


def test_consistency_basic():
    deckcount = 10
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=1,
        hand_checker=hand_is_good,
    )
    result = result.p5
    assert result in (0, 1)


def test_consistency_with_blanks_added():
    deckcount = 10
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )
    result = result.p5
    assert 0 <= result <= 1


def test_consistency_error_on_overfilled_deck():
    deckcount = 4
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]

    with pytest.raises(InvalidCardCountsError):
        simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
            ideal_hands=ideal_hands,
            num_hands=10,
            hand_checker=hand_is_good,
        )


def test_consistency_full_deck_matches_all_hands():
    deckcount = 5
    ratios = [1, 1, 1, 1, 1]
    names = ["A", "B", "C", "D", "E"]
    ideal_hands = [["A", "B", "C", "D", "E"]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )
    result = result.p5
    assert result == 1.0


def test_consistency_hand_never_matches():
    deckcount = 5
    ratios = [5]
    names = ["A"]
    ideal_hands = [["B"]]

    result = simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=10,
        hand_checker=hand_is_good,
    )
    result = result.p5
    assert result == 0.0


def test_consistency_does_not_mutate_inputs():
    deckcount = 10
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]
    ratios_copy = ratios.copy()
    names_copy = names.copy()

    simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        ideal_hands=ideal_hands,
        num_hands=5,
        hand_checker=hand_is_good,
    )

    assert ratios == ratios_copy
    assert names == names_copy