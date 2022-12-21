import enum

from dataclasses import asdict, dataclass
from typing import Optional

from autoprotocol import Container
from autoprotocol.unit import Unit


class Location(enum.Enum):
    warm_37 = enum.auto()
    warm_30 = enum.auto()
    ambient = enum.auto()
    cold_4 = enum.auto()
    cold_20 = enum.auto()
    cold_80 = enum.auto()


@dataclass
class StorageLocation:
    where: Location


@dataclass
class RefOpts:
    id: Optional[str] = None
    new: Optional[str] = None
    discard: Optional[bool] = None
    store: Optional[StorageLocation] = None
    cover: Optional[str] = None  # TODO: Make enum

    def as_dict(self):
        return self._remove_empty_fields(asdict(self))

    @staticmethod
    def _remove_empty_fields(data):
        """
        Helper function to recursively search through and pop items containing
        empty dictionaries/lists or dictionaries containing fields with None
        values

        Parameters
        ----------
        data : dict or list
            Data dictionary or list to remove empty fields from

        Returns
        -------
        dict or list
            Dictionary or list without fields with None values

        """
        # We're not checking against the generic not since there are values
        # such as `0` or False which are valid.
        def filter_criteria(item):
            # Workaround for Unit equality comparison issues
            if isinstance(item, Unit):
                return False
            return item is None or item == [] or item == {}

        if isinstance(data, dict):
            return {
                k: RefOpts._remove_empty_fields(v)
                for k, v in data.items()
                if not filter_criteria(v)
            }
        if isinstance(data, list):
            return [
                RefOpts._remove_empty_fields(_) for _ in data if not filter_criteria(_)
            ]
        return data


@dataclass
class Ref:
    name: str
    opts: RefOpts
    container: Container

    """
    Link a ref name (string) to a Container instance.

    """

    def __repr__(self):
        return f"Ref({self.name}, {self.container}, {self.opts})"
