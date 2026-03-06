from app.calculator.calculator import hand_is_good


def test_hand_matches_exact_pattern():
    hand = ["A", "K", "Q"]
    ideal_hands = [["A", "K", "Q"]]
    assert hand_is_good(hand, ideal_hands) is True


def test_hand_has_extra_cards():
    hand = ["A", "K", "Q", "J"]
    ideal_hands = [["A", "K", "Q"]]
    assert hand_is_good(hand, ideal_hands) is True


def test_hand_missing_card():
    hand = ["A", "K"]
    ideal_hands = [["A", "K", "Q"]]
    assert hand_is_good(hand, ideal_hands) is False


def test_hand_with_duplicates_matches_pattern():
    hand = ["A", "A", "K", "Q"]
    ideal_hands = [["A", "K", "Q"]]
    assert hand_is_good(hand, ideal_hands) is True


def test_hand_requires_multiple_of_same_card():
    hand = ["A", "A", "K", "Q"]
    ideal_hands = [["A", "A", "K", "Q"]]
    assert hand_is_good(hand, ideal_hands) is True


def test_hand_insufficient_duplicates():
    hand = ["A", "K", "Q"]
    ideal_hands = [["A", "A", "K", "Q"]]
    assert hand_is_good(hand, ideal_hands) is False


def test_empty_hand_and_empty_ideal():
    hand = []
    ideal_hands = [[]]
    assert hand_is_good(hand, ideal_hands) is True


def test_empty_hand_nonempty_ideal():
    hand = []
    ideal_hands = [["A"]]
    assert hand_is_good(hand, ideal_hands) is False


def test_hand_matches_one_of_multiple_patterns():
    hand = ["A", "K", "Q"]
    ideal_hands = [["A", "A", "K"], ["A", "K", "Q"], ["J", "Q", "K"]]
    assert hand_is_good(hand, ideal_hands) is True


def test_hand_matches_none_of_multiple_patterns():
    hand = ["A", "K"]
    ideal_hands = [["A", "A", "K"], ["A", "K", "Q"], ["J", "Q", "K"]]
    assert hand_is_good(hand, ideal_hands) is False
