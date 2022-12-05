from dataclasses import dataclass
from typing import Union

from container import Well, WellGroup

WellParam = Union[Well, list[Well], WellGroup]

@dataclass
class AutopickGroup:
  source: WellParam
  destination: WellParam
  min_abort: int = 0
