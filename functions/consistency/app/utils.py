from typing import Counter

from app.calculator import CardDatabase, CompiledPattern


def build_card_attribute_index(card_database: CardDatabase) -> dict[int, Counter]:
    index: dict[int, Counter] = {}

    for card_id, info in card_database.items():
        c = Counter()
        for field, value in info.items():
            if value is not None:
                c[(field, value)] += 1
        index[card_id] = c

    return index


def compile_patterns(ideal_hands) -> list[CompiledPattern]:
    """
    Convert patterns to a form optimized for matching:
    - exact: {card_id: count}
    - wild: {(field,value): count}
    Also normalizes integer strings to int.
    """
    compiled = []

    for pattern in ideal_hands:
        # Normalize pattern: convert strings that are numeric to int
        normalized = [
            c if isinstance(c, str) and c.startswith("any_") else int(c)
            for c in pattern
        ]

        # Convert to Counter
        counter = Counter(normalized)
        exact = {}
        wild = {}

        for card, count in counter.items():
            if isinstance(card, int):
                exact[card] = count
            elif isinstance(card, str) and card.startswith("any_"):
                parts = card.split("_", 2)
                if len(parts) != 3:
                    raise ValueError(f"Invalid wildcard pattern: {card}")
                _, field, value = parts
                wild[(field, value)] = count
            else:
                raise ValueError(
                    f"Invalid pattern entry: {card} ({type(card)})")

        compiled.append((exact, wild))

    return compiled
