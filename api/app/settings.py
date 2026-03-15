import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Settings
    AWS_ACCOUNT_ID: str | None = os.environ.get("AWS_ACCOUNT_ID")
    AWS_ACCESS_KEY_ID: str | None = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = "eu-west-2"
    LOCALSTACK_ENDPOINT: str | None = os.environ.get("LOCALSTACK_ENDPOINT")

    ENV_PREFIX: str = os.environ.get("ENV_PREFIX", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
