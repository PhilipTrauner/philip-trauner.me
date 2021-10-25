from dataclasses import dataclass

from pydantic import ValidationError

from .base import CommonIoFault
from .base import CommonJsonDecodeFault
from .base import ContextualizedFault


class Fault(ContextualizedFault):
    ...


class IoFault(Fault, CommonIoFault):
    ...


class JsonDecodeFault(Fault, CommonJsonDecodeFault):
    ...


@dataclass
class ValidationFault(Fault):
    context: ValidationError

    @property
    def description(self) -> str:
        c = self.context

        errors = [
            " ".join(
                (
                    e["msg"] if "msg" in e else "",
                    f"(type={e['type']})" if "type" in e else "",
                    f"(loc={e['loc'][0]})" if "loc" in e and len(e["loc"]) > 0 else "",
                )
            )
            for e in c.errors()
        ]

        additional_context = f" ({', '.join(errors)})" if len(errors) > 0 else ""
        return f"error occurred while validating model input{additional_context}"
