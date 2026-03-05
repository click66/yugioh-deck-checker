import aioboto3
import json
from typing import Dict, Any

from app.dependencies.jobs.job import Job
from app.settings import Settings


class LambdaJobRunner:
    """
    Lambda runner that supports FastAPI lifespan pattern.
    Client is initialized once and shared across all calls.
    Supports LocalStack in dev/test via LOCALSTACK_ENDPOINT env variable.
    """

    def __init__(self, function_name: str):
        self.function_name = function_name
        self._client = None
        self._session = aioboto3.Session()

    async def init_client(self, settings: Settings):
        if self._client is None:
            self._client = await self._session.client(
                "lambda",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_ENDPOINT,
            ).__aenter__()

    async def close_client(self):
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def run_job(self, job: Job) -> str:
        if not self._client:
            raise RuntimeError("Lambda client not initialized.")

        payload_with_id: Dict[str, Any] = {
            **job.payload,
            "job_id": job.job_id,
        }

        await self._client.invoke(
            FunctionName=self.function_name,
            InvocationType="Event",
            Payload=json.dumps(payload_with_id).encode("utf-8"),
        )

        return job.job_id
