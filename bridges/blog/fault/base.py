from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from typing import Generic
from typing import TypeVar

from ..util import uncapitalize


class Fault(ABC):
    @property
    @abstractmethod
    def description(self) -> str:
        ...


T = TypeVar("T", bound=Fault)


class ContextualizedFault(Generic[T], Fault):
    context: T


# Common faults
@dataclass
class CommonIoFault(ContextualizedFault):
    context: IOError

    @property
    def description(self) -> str:
        c = self.context

        additional_context = (
            f" (file: {c.filename})" if c.filename is not None else None
        )
        return f"error occurred while performing i/o{additional_context or ''}"


@dataclass
class CommonJsonDecodeFault(ContextualizedFault):
    context: JSONDecodeError

    @property
    def description(self) -> str:
        c = self.context

        additional_context = (
            f": {uncapitalize(c.msg)} "
            f"(line: {c.lineno}, column: {c.colno}, char: {c.pos})"
        )
        return f"error occurred while decoding JSON{additional_context}"
