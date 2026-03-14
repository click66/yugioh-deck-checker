import os
import boto3
import logging
import json
from app.calculator.calculator import (
    hand_is_wild,
    simple_consistency,
    run_test_hand_with_gambling,
    CardDatabase,
)

logger = logging.getLogger()
logger.setLevel("INFO")

TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"
dynamodb = boto3.client("dynamodb")

CARD_DATABASE_BUCKET_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-card-database"
CARD_DATABASE_KEY = "cards-detailed.json"
s3 = boto3.client("s3")

GAMBLING_CARDS = {
    1475311: {  # Allure of Darkness
        "draw": 2,
        # must discard one card matching this
        "discard": [("attribute", "DARK")],
    },
    70368879: {  # Upstart Goblin
        "draw": 1,
        "discard": [],
    },
}


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
    num_hands = 1_000_000  # fixed for now

    # Feature toggle: whether to use gambling
    use_gambling = event.get("use_gambling", False)

    logger.info(f"Job {job_id} started. use_gambling={use_gambling}")

    logger.info("Reading card database...")

    try:
        resp = s3.get_object(
            Bucket=CARD_DATABASE_BUCKET_NAME, Key=CARD_DATABASE_KEY)
        card_list = json.load(resp["Body"])
        # Build database keyed by integer ID
        card_database: CardDatabase = {
            int(card["id"]): card for card in card_list}
        logger.info("Card database loaded successfully from S3.")
    except Exception as e:
        logger.error(f"Failed to load card database from S3: {e}")
        card_database: CardDatabase = {}

    try:
        # Always use run_test_hand_with_gambling for consistency checks
        def hand_checker(remaining_deck, hand, ideal_counters):
            return run_test_hand_with_gambling(
                hand=hand,
                ideal_hands=ideal_counters,
                card_database=card_database,
                remaining_deck=remaining_deck,
                gambling_cards=GAMBLING_CARDS,
            ) if use_gambling else hand_is_wild(
                hand=hand,
                ideal_hands=ideal_counters,
                card_database=card_database,
            )

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
