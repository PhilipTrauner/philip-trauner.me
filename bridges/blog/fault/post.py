from dataclasses import dataclass
from pathlib import Path

from . import model
from .base import CommonIoFault
from .base import Fault as BaseFault


class Fault(BaseFault):
    ...


@dataclass
class PathFault(Fault):
    path: Path

    @property
    def description(self) -> str:
        return f"path to post does not exist ({self.path})"


class IoFault(Fault, CommonIoFault):
    ...


class MissingHeadingFault(Fault):
    @property
    def description(self) -> str:
        return "post has no heading"


@dataclass
class MetadataMissingFault(Fault):
    path: Path

    @property
    def description(self) -> str:
        return f"post metadata does not exist (expected at {self.path})"


@dataclass
class MetadataFault(Fault):
    fault: model.Fault

    def into(self) -> model.Fault:
        return self.fault

    @property
    def description(self) -> str:
        return self.fault.description
