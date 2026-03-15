import aioboto3
import json
from typing import Dict, Any
from app.dependencies.jobs.job import Job
from app.settings import Settings


def _build_queue_url(settings: Settings, name: str) -> str:
    account_id = settings.AWS_ACCOUNT_ID
    env_prefix = settings.ENV_PREFIX
    region = settings.AWS_REGION
    return f"https://sqs.{region}.amazonaws.com/{account_id}/{env_prefix}-{name}"


class SQSJobRunner:
    """
    Pushes jobs to an SQS queue.
    """

    def __init__(self, queue_name: str, settings: Settings):
        self.queue_name = queue_name
        self.settings = settings
        self._client = None
        self._session = aioboto3.Session()

    async def init_client(self):
        if self._client is None:
            kwargs = {"region_name": self.settings.AWS_REGION}
            if self.settings.LOCALSTACK_ENDPOINT:
                kwargs.update(
                    aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                    endpoint_url=self.settings.LOCALSTACK_ENDPOINT,
                )
            client = self._session.client("sqs", **kwargs)
            self._client = await client.__aenter__()

    async def close_client(self):
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def run_job(self, job: Job) -> str:
        if not self._client:
            raise RuntimeError("SQS client not initialized.")

        payload_with_id: Dict[str, Any] = {
            **job.payload,
            "job_id": job.job_id,
        }

        await self._client.send_message(
            QueueUrl=_build_queue_url(
                settings=self.settings,
                name=self.queue_name,
            ),
            MessageBody=json.dumps(payload_with_id),
        )

        return job.job_id
