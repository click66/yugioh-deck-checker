import aioboto3
import json
from typing import Dict, Any
from app.dependencies.jobs.job import Job
from app.settings import Settings


class SQSJobRunner:
    """
    Pushes jobs to an SQS queue. Works with both LocalStack and real AWS.
    """

    def __init__(self, queue_name: str, settings: Settings):
        self.queue_name = queue_name
        self.settings = settings
        self._client = None
        self._session = aioboto3.Session()

    async def init_client(self):
        if self._client is None:
            kwargs = {"region_name": self.settings.AWS_REGION}
            # Include credentials and endpoint if using LocalStack
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

    async def _get_queue_url(self) -> str:
        """
        Returns the correct SQS URL for LocalStack or AWS.
        """
        # LocalStack or real AWS, always use get_queue_url
        response = await self._client.get_queue_url(
            QueueName=f"{self.settings.ENV_PREFIX}-{self.queue_name}"
        )
        return response["QueueUrl"]

    async def run_job(self, job: Job) -> str:
        if not self._client:
            raise RuntimeError("SQS client not initialized.")

        queue_url = await self._get_queue_url()

        payload_with_id: Dict[str, Any] = {
            **job.payload,
            "job_id": job.job_id,
        }

        await self._client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload_with_id),
        )

        return job.job_id
