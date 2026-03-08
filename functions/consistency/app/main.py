import os
import boto3
import logging
import json
from app.calculator.calculator import hand_is_good, hand_is_wild, simple_consistency

logger = logging.getLogger()
logger.setLevel("INFO")

TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"
dynamodb = boto3.client("dynamodb")

CARD_DATABASE_BUCKET_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-card-database"
CARD_DATABASE_KEY = "cards-detailed.json"
s3 = boto3.client("s3")

# Minimal mock card database keyed by card ID
# card_database = {
#     80181649: {"frameType": "spell", "attribute": None, "race": None, "name": "A Case for K9"},
#     86988864: {"frameType": "effect", "attribute": None, "race": "Beast", "name": "3-Hump Lacooda"},
#     14261867: {"frameType": "effect", "attribute": "DARK", "race": "Insect", "name": "8-Claws Scorpion"},
#     23771716: {"frameType": "normal", "attribute": "WATER", "race": "Fish", "name": "7 Colored Fish"},
#     6850209: {"frameType": "spell", "attribute": "DARK", "race": "Quick-Play", "name": "A Deal with Dark Ruler"},
#     68170903: {"frameType": "trap", "attribute": None, "race": None, "name": "A Feint Plan"},
# }

# # Wildcard definitions for IDs
# wildcard_lookup = {
#     "any_spell": lambda card_id: card_database[card_id]["frameType"] == "spell",
#     "any_trap": lambda card_id: card_database[card_id]["frameType"] == "trap",
#     "any_dark": lambda card_id: card_database[card_id].get("attribute") == "DARK",
# }


def _serialize_result(result):
    if isinstance(result, (int, float)):
        return {"N": str(result)}
    elif isinstance(result, dict):
        return {"M": {k: _serialize_result(v) for k, v in result.items()}}
    elif isinstance(result, list):
        return {"L": [_serialize_result(v) for v in result]}
    elif result is None:
        return {"NULL": True}
    else:
        return {"S": str(result)}


def lambda_handler(event, context):
    job_id = event.get("job_id")
    deckcount = event["deckcount"]
    names = event["names"]
    ratios = event["ratios"]
    ideal_hands = event["ideal_hands"]
    num_hands = 10  # fixed for now # Temporarily switch to 10 test hands only

    # Feature toggle: whether to use hand_is_wild
    use_wildcards = event.get("use_wildcards", False)

    logger.info(f"Job {job_id} started. use_wildcards={use_wildcards}")

    logger.info("Reading card database...")

    try:
        resp = s3.get_object(
            Bucket=CARD_DATABASE_BUCKET_NAME, Key=CARD_DATABASE_KEY)
        card_list = json.load(resp["Body"])
        card_database = {card["id"]: card for card in card_list}
        logger.info("Card database loaded successfully from S3.")
    except Exception as e:
        logger.error(f"Failed to load card database from S3: {e}")
        card_database = {}

    try:
        if use_wildcards:
            def hand_checker(hand, ideal_counters): return hand_is_wild(
                hand,
                ideal_counters,
                card_database,
            )
        else:
            hand_checker = hand_is_good

        result = simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
            ideal_hands=ideal_hands,
            num_hands=num_hands,
            hand_checker=hand_checker,
        )
        status = "completed"
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        result = None
        status = "failed"

    logger.info("Writing result...")

    expression_attr_names = {"#s": "status"}
    expression_attr_values = {":status": {"S": status}}
    update_expression = "SET #s = :status"

    if result is not None:
        result_dict = {k: getattr(result, k)
                       for k in result.__dataclass_fields__}
        combined_result = {
            "value": str(result_dict["p5"]),
            "value_6": str(result_dict["p6"]),
        }

        update_expression += ", #r = :result"
        expression_attr_names["#r"] = "result"
        expression_attr_values[":result"] = _serialize_result(combined_result)

    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={"job_id": {"S": job_id}},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attr_names,
        ExpressionAttributeValues=expression_attr_values,
    )

    logger.info(f"Job {job_id} processed. Result written to job registry.")
