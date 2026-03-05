from contextlib import asynccontextmanager

import aioboto3
from fastapi import FastAPI
from mangum import Mangum

from app.dependencies.jobs.aws_lambda import LambdaJobRunner
from app.routers import consistency
from app.settings import get_settings


FUNCTIONS = {
    "consistency": "consistency",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    try:
        # Setup AWS Lambda and initiatilse job runners
        job_runners = {}
        for key, function_name in FUNCTIONS.items():
            runner = LambdaJobRunner(
                function_name=function_name,
                settings=settings,
            )
            await runner.init_client()
            job_runners[key] = runner
        app.state.job_runners = job_runners

        # Setup DynamoDB connection and initialise job registry
        kwargs = {"region_name": settings.AWS_REGION}

        if settings.LOCALSTACK_ENDPOINT:
            kwargs.update(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

        app.state.dynamodb_session = aioboto3.Session(**kwargs)

        yield
    finally:
        for runner in job_runners.values():
            await runner.close_client()

app = FastAPI(lifespan=lifespan)

app.include_router(consistency.router)

handler = Mangum(app)
