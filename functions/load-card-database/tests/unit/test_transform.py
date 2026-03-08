from app.transform import transform_cards, process_cards

full_card = {
    "id": 12345,
    "name": "Test Card",
    "frameType": "monster",
    "race": "Dragon",
    "archetype": "Testarchetype",
    "attribute": "LIGHT"
}

partial_card = {
    "id": 67890,
    "name": "Partial Card",
    "frameType": "spell"
}

empty_payload = {"data": []}

multiple_cards_payload = {
    "data": [
        full_card,
        partial_card
    ]
}


def test_transform_cards_full():
    # Given a card with all fields present
    cards = [full_card]

    # When transforming cards
    detailed, slim = transform_cards(cards)

    # Then slim should contain only id and name
    assert slim == [{"id": 12345, "name": "Test Card"}]

    # Then detailed should contain all fields present
    expected_detailed = {
        "id": 12345,
        "name": "Test Card",
        "frameType": "monster",
        "race": "Dragon",
        "archetype": "Testarchetype",
        "attribute": "LIGHT"
    }
    assert detailed == [expected_detailed]


def test_transform_cards_partial():
    # Given a card missing optional fields
    cards = [partial_card]

    # When transforming cards
    detailed, slim = transform_cards(cards)

    # Then slim should contain only id and name
    assert slim == [{"id": 67890, "name": "Partial Card"}]

    # Then detailed should contain only present fields
    expected_detailed = {
        "id": 67890,
        "name": "Partial Card",
        "frameType": "spell"
    }
    assert detailed == [expected_detailed]


def test_transform_cards_empty():
    # Given an empty card list
    cards = []

    # When transforming cards
    detailed, slim = transform_cards(cards)

    # Then both detailed and slim should be empty
    assert detailed == []
    assert slim == []


def test_transform_cards_multiple():
    # Given multiple cards with mixed fields
    cards = [full_card, partial_card]

    # When transforming cards
    detailed, slim = transform_cards(cards)

    # Then slim should contain only id and name
    expected_slim = [
        {"id": 12345, "name": "Test Card"},
        {"id": 67890, "name": "Partial Card"}
    ]
    assert slim == expected_slim

    # Then detailed should correctly map all present fields
    expected_detailed = [
        {
            "id": 12345,
            "name": "Test Card",
            "frameType": "monster",
            "race": "Dragon",
            "archetype": "Testarchetype",
            "attribute": "LIGHT"
        },
        {
            "id": 67890,
            "name": "Partial Card",
            "frameType": "spell"
        }
    ]
    assert detailed == expected_detailed


def test_process_cards_with_mock_fetch():
    # Given a mock fetch function returning multiple cards
    def mock_fetch():
        return multiple_cards_payload

    # When processing cards with injected fetch
    detailed, slim = process_cards(mock_fetch)

    # Then slim should match transform_cards output
    expected_slim = [
        {"id": 12345, "name": "Test Card"},
        {"id": 67890, "name": "Partial Card"}
    ]
    assert slim == expected_slim

    # Then detailed should match transform_cards output
    expected_detailed = [
        {
            "id": 12345,
            "name": "Test Card",
            "frameType": "monster",
            "race": "Dragon",
            "archetype": "Testarchetype",
            "attribute": "LIGHT"
        },
        {
            "id": 67890,
            "name": "Partial Card",
            "frameType": "spell"
        }
    ]
    assert detailed == expected_detailed


def test_process_cards_empty_fetch():
    # Given a mock fetch function returning empty data
    def mock_fetch():
        return empty_payload

    # When processing cards
    detailed, slim = process_cards(mock_fetch)

    # Then both slim and detailed should be empty
    assert slim == []
    assert detailed == []


def test_transform_cards_full():
    cards = [full_card]
    detailed, slim = transform_cards(cards)

    assert slim == [{"id": 12345, "name": "Test Card"}]

    expected_detailed = {
        "id": 12345,
        "name": "Test Card",
        "frameType": "monster",
        "superType": "monster",
        "race": "Dragon",
        "archetype": "Testarchetype",
        "attribute": "LIGHT"
    }
    assert detailed == [expected_detailed]


def test_transform_cards_partial():
    cards = [partial_card]
    detailed, slim = transform_cards(cards)

    assert slim == [{"id": 67890, "name": "Partial Card"}]

    expected_detailed = {
        "id": 67890,
        "name": "Partial Card",
        "frameType": "spell",
        "superType": "spell"
    }
    assert detailed == [expected_detailed]


def test_transform_cards_empty():
    cards = []
    detailed, slim = transform_cards(cards)

    assert detailed == []
    assert slim == []


def test_transform_cards_multiple():
    cards = [full_card, partial_card]
    detailed, slim = transform_cards(cards)

    expected_slim = [
        {"id": 12345, "name": "Test Card"},
        {"id": 67890, "name": "Partial Card"}
    ]
    assert slim == expected_slim

    expected_detailed = [
        {
            "id": 12345,
            "name": "Test Card",
            "frameType": "monster",
            "superType": "monster",
            "race": "Dragon",
            "archetype": "Testarchetype",
            "attribute": "LIGHT"
        },
        {
            "id": 67890,
            "name": "Partial Card",
            "frameType": "spell",
            "superType": "spell"
        }
    ]
    assert detailed == expected_detailed


def test_process_cards_with_mock_fetch():
    def mock_fetch():
        return multiple_cards_payload

    detailed, slim = process_cards(mock_fetch)

    expected_slim = [
        {"id": 12345, "name": "Test Card"},
        {"id": 67890, "name": "Partial Card"}
    ]
    assert slim == expected_slim

    expected_detailed = [
        {
            "id": 12345,
            "name": "Test Card",
            "frameType": "monster",
            "superType": "monster",
            "race": "Dragon",
            "archetype": "Testarchetype",
            "attribute": "LIGHT"
        },
        {
            "id": 67890,
            "name": "Partial Card",
            "frameType": "spell",
            "superType": "spell"
        }
    ]
    assert detailed == expected_detailed


def test_process_cards_empty_fetch():
    def mock_fetch():
        return empty_payload

    detailed, slim = process_cards(mock_fetch)

    assert slim == []
    assert detailed == []
