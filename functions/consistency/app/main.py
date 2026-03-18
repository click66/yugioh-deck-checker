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
from app.calculator.data import GAMBLING_CARDS
from app.utils import build_card_attribute_index, compile_patterns

logger = logging.getLogger()
logger.setLevel("INFO")

TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"

CARD_DATABASE_BUCKET_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-card-database"
CARD_DATABASE_KEY = "cards-detailed.json"


def _get_dynamodb_client():
    return boto3.client("dynamodb")


def _get_s3_client():
    return boto3.client("s3")


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


def _load_card_database_s3() -> CardDatabase:
    s3 = _get_s3_client()
    resp = s3.get_object(Bucket=CARD_DATABASE_BUCKET_NAME,
                         Key=CARD_DATABASE_KEY)
    card_list = json.load(resp["Body"])
    return {int(card["id"]): card for card in card_list}


def _load_card_database_local(path: str) -> CardDatabase:
    with open(path, "r", encoding="utf-8") as f:
        card_list = json.load(f)
    return {int(card["id"]): card for card in card_list}


def run_calculation(
    deckcount,
    names,
    ratios,
    ideal_hands,
    card_database,
    use_gambling,
):
    card_attribute_index = build_card_attribute_index(card_database)
    compiled_hands = compile_patterns(ideal_hands)
    num_hands = 1_000_000

    def hand_tester(remaining_deck, hand):
        def hand_checker(hand, compiled=compiled_hands):
            return hand_is_wild(hand, compiled, card_attribute_index)

        if use_gambling:
            return run_test_hand_with_gambling(
                hand_checker=hand_checker,
                hand=hand,
                card_attr_index=card_attribute_index,
                remaining_deck=remaining_deck,
                gambling_cards=GAMBLING_CARDS,
            )
        else:
            return run_test_hand_without_gambling(hand_checker=hand_checker, hand=hand)

    return simple_consistency(
        deckcount=deckcount,
        ratios=ratios,
        names=names,
        num_hands=num_hands,
        hand_tester=hand_tester,
    )


def event_handler(event):
    job_id = event.get("job_id")
    deckcount = event["deckcount"]
    names = event["names"]
    ratios = event["ratios"]
    ideal_hands = event["ideal_hands"]
    use_gambling = event.get("use_gambling", False)

    logger.info(f"Job {job_id} started. use_gambling={use_gambling}")
    logger.info("Reading card database...")

    try:
        card_database = _load_card_database_s3()
        logger.info("Card database loaded successfully from S3.")
    except Exception as e:
        logger.error(f"Failed to load card database from S3: {e}")
        card_database = {}

    try:
        result = run_calculation(
            deckcount=deckcount,
            names=names,
            ratios=ratios,
            ideal_hands=ideal_hands,
            card_database=card_database,
            use_gambling=use_gambling,
        )
        status = "completed"
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        result = None
        status = "failed"

    logger.info("Writing result...")
    dynamodb = _get_dynamodb_client()

    expression_attr_names = {"#s": "status"}
    expression_attr_values = {":status": {"S": status}}
    update_expression = "SET #s = :status"

    if result is not None:
        result_dict = {k: getattr(result, k)
                       for k in result.__dataclass_fields__}

        def serialize_counter(counter: Counter[int]) -> dict:
            return {str(k): v for k, v in counter.items()}

        combined_result = {
            "used_gambling": f"{int(use_gambling)}",
            "p5": result_dict["p5"],
            "p6": result_dict["p6"],
            "p5_with_gambling": result_dict["p5_with_gambling"],
            "p6_with_gambling": result_dict["p6_with_gambling"],
            "rescued_5": result_dict["rescued_5"],
            "rescued_6": result_dict["rescued_6"],
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
            "near_miss_counts": serialize_counter(result_dict.get("near_miss_counts", Counter())),
            "blocking_card_counts": serialize_counter(result_dict.get("blocking_card_counts", Counter())),
            "ideal_hand_counts": serialize_counter(result_dict.get("ideal_hand_counts", Counter())),
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


def lambda_handler(event, context):
    for record in event.get("Records", []):
        try:
            payload = json.loads(record["body"])
            logger.info(f"Received new job: {json.dumps(payload, indent=2)}")
            event_handler(payload)
        except Exception as e:
            logger.error(f"Failed to process SQS record: {record}")
            logger.exception(e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run calculator locally")
    parser.add_argument("--deckcount", type=int, required=True)
    parser.add_argument("--names", type=str, required=True)
    parser.add_argument("--ratios", type=str, required=True)
    parser.add_argument("--ideal_hands", type=str, required=True)
    parser.add_argument("--card_db", type=str, required=True)
    parser.add_argument("--use_gambling", action="store_true")

    args = parser.parse_args()

    card_database = _load_card_database_local(args.card_db)

    result = run_calculation(
        deckcount=args.deckcount,
        names=json.loads(args.names),
        ratios=json.loads(args.ratios),
        ideal_hands=json.loads(args.ideal_hands),
        card_database=card_database,
        use_gambling=args.use_gambling,
    )

    result_dict = {k: getattr(result, k) for k in result.__dataclass_fields__}

    print(json.dumps(result_dict, indent=2))
