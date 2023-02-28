import dataclasses

from typing import Any

from autoprotocol.unit import unit_as_strings_factory


def asdict(data: Any):
    """
    Adds dict_factory to override dataclass default behavior when converting
    a dataclass to a dict
    """
    return dataclasses.asdict(data, dict_factory=unit_as_strings_factory)
