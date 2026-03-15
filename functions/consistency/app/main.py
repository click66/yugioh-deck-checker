import os
from typing import Counter

import boto3
import logging
import json
from app.calculator.calculator import (
    hand_is_wild,
    simple_consistency,
    run_test_hand_with_gambling,
    run_test_hand_without_gambling,
    CardDatabase,
)
from app.utils import build_card_attribute_index, compile_patterns

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
    num_hands = 1_000_000  # fixed for now

    # Feature toggle: whether to use gambling
    use_gambling = event.get("use_gambling", False)

    logger.info(f"Job {job_id} started. use_gambling={use_gambling}")

    logger.info("Reading card database...")

    # Read and compile card database
    try:
        resp = s3.get_object(
            Bucket=CARD_DATABASE_BUCKET_NAME, Key=CARD_DATABASE_KEY)
        card_list = json.load(resp["Body"])
        card_database: CardDatabase = {
            int(card["id"]): card for card in card_list}
        card_attribute_index = build_card_attribute_index(card_database)
        compiled_hands = compile_patterns(ideal_hands)
        logger.info("Card database loaded successfully from S3.")
    except Exception as e:
        logger.error(f"Failed to load card database from S3: {e}")
        card_database: CardDatabase = {}
        card_attribute_index = []
        compiled_hands = []

    try:
        def hand_tester(remaining_deck, hand):
            def hand_checker(hand, compiled=compiled_hands):
                return hand_is_wild(
                    hand,
                    compiled,
                    card_attribute_index,
                )

            if use_gambling:
                return run_test_hand_with_gambling(
                    hand_checker=hand_checker,
                    hand=hand,
                    card_attr_index=card_attribute_index,
                    remaining_deck=remaining_deck,
                    gambling_cards=GAMBLING_CARDS,
                )
            else:
                return run_test_hand_without_gambling(
                    hand_checker=hand_checker,
                    hand=hand,
                )

        result = simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
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
        # Convert the dataclass to a dict
        result_dict = {k: getattr(result, k)
                       for k in result.__dataclass_fields__}

        # Convert Counters to string-keyed dicts for DynamoDB
        def serialize_counter(counter: Counter[int]) -> dict:
            return {str(k): v for k, v in counter.items()}

        combined_result = {
            # Meta
            "used_gambling": f"{int(use_gambling)}",

            # Probabilities
            "p5": result_dict["p5"],
            "p6": result_dict["p6"],
            "p5_with_gambling": result_dict["p5_with_gambling"],
            "p6_with_gambling": result_dict["p6_with_gambling"],

            # Rescued hands
            "rescued_5": result_dict["rescued_5"],
            "rescued_6": result_dict["rescued_6"],

            # Gamble metrics
            "useful_gambles_5": serialize_counter(result_dict.get("useful_gambles_5", Counter())),
            "useful_gambles_6": serialize_counter(result_dict.get("useful_gambles_6", Counter())),
            "gamble_seen_5": serialize_counter(result_dict.get("gamble_seen_5", Counter())),
            "gamble_seen_6": serialize_counter(result_dict.get("gamble_seen_6", Counter())),
            "gamble_attempted_5": result_dict.get("gamble_attempted_5", 0),
            "gamble_attempted_6": result_dict.get("gamble_attempted_6", 0),
            "gamble_failed_5": result_dict.get("failed_gambles_5", 0),
            "gamble_failed_6": result_dict.get("failed_gambles_6", 0),
            "gamble_unplayable_5": result_dict.get("unplayable_gambles_5", 0),
            "gamble_unplayable_6": result_dict.get("unplayable_gambles_6", 0),
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
