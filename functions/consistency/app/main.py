# functions/consistency/app/main.py
import asyncio
from app.calculator.calculator import simple_consistency
from app.exceptions import Error
import aioboto3
import os

TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"


async def write_result(job_id: str, result: float):
    async with aioboto3.client("dynamodb") as client:
        await client.update_item(
            TableName=TABLE_NAME,
            Key={"job_id": {"S": job_id}},
            UpdateExpression="SET #r = :val, #s = :status",
            ExpressionAttributeNames={"#r": "result", "#s": "status"},
            ExpressionAttributeValues={
                ":val": {"N": str(result)},
                ":status": {"S": "completed"}
            }
        )


def lambda_handler(event, _):
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
    except Error as e:
        print(f"Job {job_id} failed: {e}")
        result = None

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        result = None

    if result is not None:
        asyncio.run(write_result(job_id, result))

    print(f"Job {job_id} processed. Result written to DynamoDB.")
