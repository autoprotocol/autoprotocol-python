from dataclasses import dataclass
from typing import Union

from container import Well, WellGroup

WellParam = Union[Well, list[Well], WellGroup]
AutopickGroupTuple = tuple[WellParam, WellParam, int]

@dataclass
class AutopickGroupClass:
  source: WellParam
  destination: WellParam
  min_abort: int = 0
