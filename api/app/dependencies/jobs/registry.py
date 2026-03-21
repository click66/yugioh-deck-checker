import time
from typing import AsyncGenerator

from botocore.config import Config
from boto3.dynamodb.types import TypeDeserializer
from fastapi import Request

from app.dependencies.jobs.job import BatchJob, Job
from app.settings import get_settings

TABLE_NAME = "jobs"
BATCH_INDEX = "batch_id-index"

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
            result=deserialized.get("result", None),
            error=deserialized.get("error"),
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

    async def create_batch(
        self,
        batch: BatchJob,
        ttl_seconds: int = 600,
    ) -> str:
        """Create all jobs in a supplied batch"""
        now = int(time.time())

        for job in batch.jobs:
            item = {
                "job_id": {"S": job.job_id},
                "payload": {"S": str(job.payload)},
                "ttl": {"N": str(now + ttl_seconds)},
                "status": {"S": job.status},
                "created_at": {"N": str(int(job.created_at.timestamp()))},
                "batch_id": {"S": batch.batch_id},
            }

            await self._client.put_item(
                TableName=self._table_name,
                Item=item,
            )

        return batch.batch_id

    async def get_batch_job(self, batch_id: str) -> BatchJob:
        resp = await self._client.query(
            TableName=self._table_name,
            IndexName=BATCH_INDEX,
            KeyConditionExpression="batch_id = :b",
            ExpressionAttributeValues={
                ":b": {"S": batch_id},
            },
        )

        items = resp.get("Items", [])

        jobs: list[Job] = []

        for item in items:
            d = {k: deserializer.deserialize(v) for k, v in item.items()}

            jobs.append(
                Job(
                    job_id=d.get("job_id"),
                    payload=d.get("payload", {}),
                    status=d.get("status", "pending"),
                    created_at=d.get("created_at"),
                    completed_at=d.get("completed_at"),
                    result=d.get("result"),
                    error=d.get("error"),
                )
            )

        return BatchJob(
            batch_id=batch_id,
            jobs=jobs,
        )


async def get_job_registry(request: Request) -> AsyncGenerator[DynamoJobRegistry, None]:
    session = request.app.state.dynamodb_session
    settings = get_settings()

    client_kwargs = {
        "service_name": "dynamodb",
        "config": Config(
            connect_timeout=5.0,
            read_timeout=10.0,
            retries={"max_attempts": 3},
        ),
    }

    if settings.LOCALSTACK_ENDPOINT:
        client_kwargs["endpoint_url"] = settings.LOCALSTACK_ENDPOINT

    async with session.client(**client_kwargs) as dynamodb_client:
        registry = DynamoJobRegistry(
            f'{settings.ENV_PREFIX}-{TABLE_NAME}',
            dynamodb_client,
        )
        yield registry
