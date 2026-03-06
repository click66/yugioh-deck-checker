# functions/consistency/app/main.py
import os
import boto3
from app.calculator.calculator import simple_consistency

TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"
dynamodb = boto3.client("dynamodb")


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
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        result = None

    if result is not None:
        dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={"job_id": {"S": job_id}},
            UpdateExpression="SET #r = :val, #s = :status",
            ExpressionAttributeNames={"#r": "result", "#s": "status"},
            ExpressionAttributeValues={
                ":val": {"N": str(result)},
                ":s": {"S": "completed"},
            },
        )

    print(f"Job {job_id} processed. Result written to DynamoDB.")
