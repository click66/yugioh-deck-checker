import os
from typing import Counter

import boto3
import logging
import json
from app.calculator.calculator import (
    hand_is_wild,
    simple_consistency,
    run_test_hand_with_gambling,
    CardDatabase,
)
from app.calculator.result import HandTestResult

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
    20508881: {  # Radiant Typhoon Vision
        "draw": 2,
        "discard": [("race", "Quick-Play")],
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
    num_hands = 20  # fixed for now

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
        def hand_tester(remaining_deck, hand, ideal_counters):
            if use_gambling:
                # Returns a full HandTestResult with gambling metrics
                return run_test_hand_with_gambling(
                    hand_checker=hand_is_wild,
                    hand=hand,
                    ideal_hands=ideal_counters,
                    card_database=card_database,
                    remaining_deck=remaining_deck,
                    gambling_cards=GAMBLING_CARDS,
                )
            else:
                # Wrap boolean return in HandTestResult with defaults for gambling stats
                result = hand_is_wild(
                    hand=hand,
                    ideal_hands=ideal_counters,
                    card_database=card_database,
                )
                return HandTestResult(
                    matches_without_gambling=result,
                    matches_with_gambling=result,
                    rescued_with_gambling=0,
                    useful_gambles=Counter(),
                    failed_gamble_attempts=0,
                )

        result = simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
            ideal_hands=ideal_hands,
            num_hands=num_hands,
            hand_tester=hand_tester,
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
        # Serialize all metrics from the result dataclass
        result_dict = {k: getattr(result, k)
                       for k in result.__dataclass_fields__}

        # Include all metrics, renamed for clarity if needed
        combined_result = {
            "p5": result_dict.get("p5"),
            "p6": result_dict.get("p6"),
            "rescued_5": result_dict.get("rescued_5"),
            "rescued_6": result_dict.get("rescued_6"),
            "failed_gambles_5": result_dict.get("failed_gambles_5"),
            "failed_gambles_6": result_dict.get("failed_gambles_6"),
            # Counter -> dict
            "useful_gambles": dict(result_dict.get("useful_gambles", {})),
        }

        # Add optional extended metrics for full insight
        # These depend on HandTestResult being returned by your hand_tester
        if hasattr(result, "gamble_seen_5"):
            combined_result.update({
                "gamble_seen_5": dict(result.gamble_seen_5),
                "gamble_seen_6": dict(result.gamble_seen_6),
                "gamble_attempted_5": result.gamble_attempted_5,
                "gamble_attempted_6": result.gamble_attempted_6,
                "gamble_failed_5": result.gamble_failed_5,
                "gamble_failed_6": result.gamble_failed_6,
                "gamble_unplayable_5": result.gamble_unplayable_5,
                "gamble_unplayable_6": result.gamble_unplayable_6,
            })

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
