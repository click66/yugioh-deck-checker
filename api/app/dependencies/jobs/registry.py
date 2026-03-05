import time
from typing import AsyncGenerator

from botocore.config import Config
from boto3.dynamodb.types import TypeDeserializer
from fastapi import Request

from app.dependencies.jobs.job import Job
from app.settings import get_settings

TABLE_NAME = "jobs"

deserializer = TypeDeserializer()


class DynamoJobRegistry:
    def __init__(self, table_name: str, client):
        self._table_name = table_name
        self._client = client

    async def get_job(self, job_id: str) -> Job | None:
        """Retrieve a job by ID and return as a Job object."""
        resp = await self._client.get_item(
            TableName=self._table_name,
            Key={"job_id": {"S": job_id}}
        )
        item = resp.get("Item")
        if not item:
            return None

        deserialized = {
            k: deserializer.deserialize(v) for k, v in item.items()
        }

        return Job(
            job_id=deserialized.get("job_id"),
            payload=deserialized.get("payload", {}),
            status=deserialized.get("status", "pending"),
            created_at=deserialized.get("created_at"),
            completed_at=deserialized.get("completed_at"),
            result=deserialized.get("result", {}),
        )

    async def create_job(self, job: Job, ttl_seconds: int = 600):
        """Create a new job."""
        now = int(time.time())
        await self._client.put_item(
            TableName=self._table_name,
            Item={
                "job_id": {"S": job.job_id},
                "payload": {"S": str(job.payload)},
                "ttl": {"N": str(now + ttl_seconds)},
                "status": {"S": "pending"},
                "created_at": {"N": str(now)},
            }
        )


async def get_job_registry(request: Request) -> AsyncGenerator[DynamoJobRegistry, None]:
    session = request.app.state.dynamodb_session
    async with session.client(
        "dynamodb",
        endpoint_url=get_settings().AWS_ENDPOINT,
        config=Config(
            connect_timeout=5.0,
            read_timeout=10.0,
            retries={"max_attempts": 3},
        )
    ) as dynamodb_client:
        registry = DynamoJobRegistry(TABLE_NAME, dynamodb_client)
        yield registry
