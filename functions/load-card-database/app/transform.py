def transform_cards(cards):
    detailed = []
    slim = []

    for card in cards:
        slim.append({
            "id": card["id"],
            "name": card["name"]
        })

        fields = ["id", "frameType", "name", "race", "archetype", "attribute"]
        obj = {f: card[f] for f in fields if f in card}

        frame_type = card.get("frameType", "").lower()
        if frame_type == "spell":
            obj["superType"] = "spell"
        elif frame_type == "trap":
            obj["superType"] = "trap"
        else:
            obj["superType"] = "monster"

        detailed.append(obj)

    return detailed, slim


def process_cards(fetch_cards):
    """
    fetch_cards: injected function returning the API payload
    """
    payload = fetch_cards()
    cards = payload.get("data", [])

    detailed, slim = transform_cards(cards)

    return detailed, slim
