import os
import boto3
import logging
from app.calculator.calculator import simple_consistency
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel("INFO")

TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"
dynamodb = boto3.client("dynamodb")


def _serialize_result(result):
    """
    Convert numeric or nested Python objects to DynamoDB-compatible format.
    DynamoDB expects numbers as Decimal and dicts/lists recursively converted.
    """
    if isinstance(result, (int, float)):
        return {"N": str(result)}
    elif isinstance(result, dict):
        return {"M": {k: _serialize_result(v) for k, v in result.items()}}
    elif isinstance(result, list):
        return {"L": [_serialize_result(v) for v in result]}
    elif result is None:
        return {"NULL": True}
    else:
        # fallback to string representation
        return {"S": str(result)}


def lambda_handler(event, context):
    job_id = event.get("job_id")
    deckcount = event["deckcount"]
    names = event["names"]
    ratios = event["ratios"]
    ideal_hands = event["ideal_hands"]
    num_hands = event.get("num_hands", 100_000)

    try:
        result = simple_consistency(
            deckcount=deckcount,
            ratios=ratios,
            names=names,
            ideal_hands=ideal_hands,
            num_hands=num_hands,
        )
        status = "completed"
    except Exception as e:
        logger.info(f"Job {job_id} failed: {e}")
        result = None
        status = "failed"

    update_expression = "SET #s = :status"
    expression_attr_names = {"#s": "status"}
    expression_attr_values = {":status": {"S": status}}

    if result is not None:
        update_expression += ", #r = :result"
        expression_attr_names["#r"] = "result"
        expression_attr_values[":result"] = _serialize_result(result)

    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={"job_id": {"S": job_id}},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attr_names,
        ExpressionAttributeValues=expression_attr_values,
    )

    logger.info(f"Job {job_id} processed. Result written to job registry.")
