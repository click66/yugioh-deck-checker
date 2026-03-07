import hashlib
import json
import urllib.request
import os

import boto3
from datetime import datetime
from app.transform import process_cards

SOURCE_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"

DATA_BUCKET = f"{os.environ.get('ENV_PREFIX', 'dev')}-card-database"
FRONTEND_BUCKET = f"{os.environ.get('ENV_PREFIX', 'dev')}-frontend"


TABLE_NAME = f"{os.environ.get('ENV_PREFIX', 'dev')}-jobs"

s3 = boto3.client("s3")


def fetch_cards_from_api():
    with urllib.request.urlopen(SOURCE_URL) as response:
        return json.loads(response.read())


def upload_to_s3(bucket, key, data, extra_args=None):
    args = {"Bucket": bucket, "Key": key, "Body": json.dumps(
        data), "ContentType": "application/json"}
    if extra_args:
        args.update(extra_args)
    s3.put_object(**args)


def lambda_handler(event, context):
    # Process cards
    detailed, slim = process_cards(fetch_cards_from_api)

    # Upload detailed and slim to main data bucket
    upload_to_s3(DATA_BUCKET, "cards-detailed.json", detailed)
    upload_to_s3(DATA_BUCKET, "cards-slim.json", slim)

    # Compute hash for cache-busting filename
    slim_bytes = json.dumps(slim).encode("utf-8")
    hash_str = hashlib.sha256(slim_bytes).hexdigest()[:8]
    date_str = datetime.utcnow().strftime("%Y%m%d")
    slim_filename = f"database-{date_str}-{hash_str}.json"
    slim_path = f"data/{slim_filename}"

    # Upload slim file to frontend bucket
    upload_to_s3(FRONTEND_BUCKET, slim_path, slim)

    # Update manifest file pointing to latest slim
    manifest = {"file": slim_filename}
    upload_to_s3(
        FRONTEND_BUCKET,
        "database-latest.json",
        manifest,
        extra_args={
            "CacheControl": "no-cache, no-store, must-revalidate",
            "Expires": "0"
        }
    )

    return {
        "cards_processed": len(slim),
        "frontend_slim_file": slim_path
    }
