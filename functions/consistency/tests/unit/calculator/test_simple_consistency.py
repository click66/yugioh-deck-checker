import pytest
from app.calculator.calculator import simple_consistency
from app.calculator.exceptions import InvalidCardCountsError


def test_consistency_basic():
    # Given a small deck and ideal hand
    deckcount = 10
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]

    # When we simulate 1 hand
    result = simple_consistency(
        deckcount, ratios, names, ideal_hands, num_hands=1)

    # Then the result should be either 0 or 1
    assert result in (0, 1)


def test_consistency_with_blanks_added():
    # Given a deck smaller than deckcount
    deckcount = 10
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]

    # When we simulate multiple hands
    result = simple_consistency(
        deckcount, ratios, names, ideal_hands, num_hands=10)

    # Then the result should always be between 0 and 1
    assert 0 <= result <= 1


def test_consistency_error_on_overfilled_deck():
    # Given ratios summing more than deckcount
    deckcount = 4
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]

    # When we try to simulate hands
    # Then a ValueError should be raised
    with pytest.raises(InvalidCardCountsError):
        simple_consistency(deckcount, ratios, names, ideal_hands, num_hands=10)


def test_consistency_full_deck_matches_all_hands():
    # Given a deck exactly matching the ideal hand
    deckcount = 5
    ratios = [1, 1, 1, 1, 1]
    names = ["A", "B", "C", "D", "E"]
    ideal_hands = [["A", "B", "C", "D", "E"]]

    # When we simulate hands
    result = simple_consistency(
        deckcount, ratios, names, ideal_hands, num_hands=10)

    # Then every hand should match (result == 1.0)
    assert result == 1.0


def test_consistency_hand_never_matches():
    # Given a deck with only one type of card
    deckcount = 5
    ratios = [5]
    names = ["A"]
    ideal_hands = [["B"]]  # impossible to draw a B

    # When we simulate hands
    result = simple_consistency(
        deckcount, ratios, names, ideal_hands, num_hands=10)

    # Then no hand should match (result == 0.0)
    assert result == 0.0


def test_consistency_does_not_mutate_inputs():
    # Given original ratios and names
    deckcount = 10
    ratios = [2, 3]
    names = ["A", "B"]
    ideal_hands = [["A", "B"]]
    ratios_copy = ratios.copy()
    names_copy = names.copy()

    # When we run the consistency function
    simple_consistency(deckcount, ratios, names, ideal_hands, num_hands=5)

    # Then the original ratios and names should remain unchanged
    assert ratios == ratios_copy
    assert names == names_copy
