from dataclasses import dataclass
from typing import List, Union

from ..container import Well, WellGroup


WellParam = Union[Well, List[Well], WellGroup]


@dataclass
class AutopickGroup:
    source: WellParam
    destination: WellParam
    min_abort: int = 0
