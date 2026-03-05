from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
