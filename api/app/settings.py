import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Settings
    AWS_ACCESS_KEY_ID: str | None = os.environ.get("AWS_ACCESS_KEY_ID", "test")
    AWS_SECRET_ACCESS_KEY: str | None = os.environ.get(
        "AWS_SECRET_ACCESS_KEY",
        "test",
    )
    AWS_REGION: str = "eu-west-2"
    AWS_ENDPOINT: str | None = os.environ.get("LOCALSTACK_ENDPOINT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
