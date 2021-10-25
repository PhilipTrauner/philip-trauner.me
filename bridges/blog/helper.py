from json import loads as json_loads
from json.decoder import JSONDecodeError
from typing import TextIO
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError
from result import Err
from result import Ok
from result import Result

from .fault import model

T = TypeVar("T", bound=BaseModel)


class ConfiguredBaseModel(BaseModel):
    @classmethod
    def new(cls: Type[T], file_like: TextIO) -> Result[T, model.Fault]:
        try:
            raw = file_like.read()
        except IOError as e:
            return Err(model.IoFault(e))

        try:
            parsed = json_loads(raw)
        except JSONDecodeError as e:
            return Err(model.JsonDecodeFault(e))

        try:
            instance = cls.parse_obj(parsed)
        except ValidationError as e:
            return Err(model.ValidationFault(e))
        else:
            return Ok(instance)

    class Config:
        allow_mutation = False
        extra = "forbid"
