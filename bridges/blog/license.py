from typing import Tuple
from dataclasses import dataclass
from enum import Enum

from .util import Url

LICENSE_VERSION = "4.0"

LICENSE_BASE_URL = "https://creativecommons.org/licenses/"
LICENSE_END_URL = f"{LICENSE_VERSION}/"

LICENSE_IMAGE_BASE_URL = "https://licensebuttons.net/i/l/"
LICENSE_IMAGE_END_URL = "transparent/00/00/00/88x31.png"


def _cc_license_urls(license_string: str) -> Tuple[Url, Url]:
    return (
        Url(LICENSE_BASE_URL) / license_string / LICENSE_END_URL,
        Url(LICENSE_IMAGE_BASE_URL) / license_string / LICENSE_IMAGE_END_URL,
    )


@dataclass(frozen=True)
class License:
    name: str
    description_url: Url


class TextLicense(License):
    def __init__(self, name: str, description_url: Url, image_url: Url) -> None:
        super().__init__(name, description_url)
        self.image_url = image_url


class CodeLicense(License):
    def __init__(self, name: str, description_url: Url) -> None:
        super().__init__(name, description_url)


class KeyConstructableEnum(Enum):
    # The `__new__` method of
    @classmethod
    def _missing_(cls, value):  # type: ignore
        super_missing = super()._missing_(value)
        if super_missing is None:
            # "by-nc-nd" -> "BY_NC_ND"
            adapted_key = value.upper().replace("-", "_")
            return cls.__members__.get(adapted_key, None)
        else:
            return super_missing


class TextLicenses(KeyConstructableEnum):
    BY_NC_ND = TextLicense(
        "Attribution-NonCommercial-NoDerivatives 4.0 International",
        *_cc_license_urls("by-nc-nd"),
    )
    BY_NC_SA = TextLicense(
        "Attribution-NonCommercial-ShareAlike 4.0 International",
        *_cc_license_urls("by-nc-sa"),
    )
    BY_NC = TextLicense(
        "Attribution-NonCommercial 4.0 International", *_cc_license_urls("by-nc")
    )
    BY_ND = TextLicense(
        "Attribution-NoDerivatives 4.0 International", *_cc_license_urls("by-nd")
    )
    BY_SA = TextLicense(
        "Attribution-ShareAlike 4.0 International", *_cc_license_urls("by-sa")
    )
    BY = TextLicense("Attribution 4.0 International", *_cc_license_urls("by"))


class CodeLicenses(KeyConstructableEnum):
    AGPL_V3 = CodeLicense(
        "AGLPv3", Url("https://choosealicense.com/licenses/agpl-3.0/")
    )
    GPL_V3 = CodeLicense("GPLv3", Url("https://choosealicense.com/licenses/gpl-3.0/"))
    LGPL_V3 = CodeLicense(
        "LGPLv3", Url("https://choosealicense.com/licenses/lgpl-3.0/")
    )
    MIT = CodeLicense("MIT", Url("https://choosealicense.com/licenses/mit/"))
    UNLICENSE = CodeLicense(
        "Unlicense", Url("https://choosealicense.com/licenses/unlicense/")
    )
    UNLICENSED = None
