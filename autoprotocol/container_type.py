"""
Container-type object and associated functions

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

import os
import requests
import re

from .container import Well
from .unit import Unit


class ContainerType:
    """
    The ContainerType class holds the capabilities and properties of a
    particular container type.

    Parameters
    ----------
    shortname : str
      Short name used to refer to a ContainerType.
    """

    container_types = {}

    def __init__(self, shortname):
        self.shortname = shortname

        if self.shortname in ContainerType.container_types:
            response = ContainerType.container_types[self.shortname]
        else:
            baseUrl = os.getenv(
                "CONTAINER_TYPES_URL", "https://secure.strateos.com/api/container_types"
            )
            url = baseUrl + "/" + shortname
            response = requests.get(url)
            ContainerType.container_types[self.shortname] = response

        attributes = response.json()["data"]["attributes"]

        for (k, v) in attributes.items():
            if v != None and k.endswith("_mm"):
                v = float(v)
            elif v != None and k.endswith("_ul"):
                v = Unit(v, "microliter")
            self.__dict__[k] = v

    def __getattr__(self, name):
        print(self.shortname + ": unknow " + name + " attribute, returning None")
        if name.endswith("_mm"):
            return 0.0
        elif name.endswith("_ul"):
            return Unit(0.0, "microliter")
        return None

    @staticmethod
    def reset_cache():
        ContainerType.container_types = {}

    @staticmethod
    def well_from_coordinates_static(row, row_count, col, col_count):
        if row >= row_count:
            raise ValueError(
                f"0-indexed row {row} is outside of the bounds of {row_count}"
            )

        if col >= col_count:
            raise ValueError(
                f"0-indexed column {col} is outside of the bounds of {col_count}"
            )

        return row * col_count + col

    def well_from_coordinates(self, row, column):
        """
        Gets the well at 0-indexed position (row, column) within the container.
        The origin is in the top left corner.

        Parameters
        ----------
        row : int
            The 0-indexed row index of the well to be fetched
        column : int
            The 0-indexed column index of the well to be fetched

        Returns
        -------
        Int
            The robotized index of the well at at position (row, column)

        Raises
        ------
        ValueError
            if the specified row is outside the bounds of the container_type
        ValueError
            if the specified column is outside the bounds of the container_type
        """
        return ContainerType.well_from_coordinates_static(
            row, self.row_count(), column, self.col_count
        )

    @staticmethod
    def robotize_static(well_ref, well_count, col_count):
        if isinstance(well_ref, list):
            return [
                ContainerType.robotize_static(well, well_count, col_count)
                for well in well_ref
            ]

        if not isinstance(well_ref, (str, int, Well)):
            raise TypeError(
                f"ContainerType.robotize(): Well reference "
                f"({well_ref}) given is not of type 'str', 'int', "
                f"or 'Well'."
            )

        if isinstance(well_ref, Well):
            well_ref = well_ref.index
        well_ref = str(well_ref)
        m = re.match(r"([a-z])([a-z]?)(\d+)$", well_ref, re.I)
        if m:
            row = ord(m.group(1).upper()) - ord("A")
            if m.group(2):
                row = 26 * (row + 1) + ord(m.group(2).upper()) - ord("A")
            col = int(m.group(3)) - 1
            row_count = well_count // col_count
            return ContainerType.well_from_coordinates_static(
                row, row_count, col, col_count
            )
        else:
            m = re.match(r"\d+$", well_ref)
            if m:
                well_num = int(m.group(0))
                # Check bounds
                if well_num >= well_count or well_num < 0:
                    raise ValueError(
                        "ContainerType.robotize(): Well number "
                        "given exceeds container dimensions."
                    )
                return well_num
            else:
                raise ValueError(
                    "ContainerType.robotize(): Well must be in "
                    "'A1' format or be an integer."
                )

    def robotize(self, well_ref):
        """
        Return a robot-friendly well reference from a number of well reference
        formats.

        Example Usage:

        .. code-block:: python

            >>> p = Protocol()
            >>> my_plate = p.ref("my_plate", cont_type="6-flat", discard=True)
            >>> my_plate.robotize("A1")
            0
            >>> my_plate.robotize("5")
            5
            >>> my_plate.robotize(my_plate.well(3))
            3
            >>> my_plate.robotize(["A1", "A2"])
            [0, 1]

        Parameters
        ----------
        well_ref : str, int, Well, list[str or int or Well]
            Well reference to be robotized in string, integer or Well object
            form. Also accepts lists of str, int or Well.

        Returns
        -------
        int or list
            Single or list of Well references passed as row-wise integer
            (left-to-right, top-to-bottom, starting at 0 = A1).

        Raises
        ------
        TypeError
            If well reference given is not an accepted type.
        ValueError
            If well reference given exceeds container dimensions.
        ValueError
            If well reference given is in an invalid format.
        """
        return ContainerType.robotize_static(well_ref, self.well_count, self.col_count)

    @staticmethod
    def humanize_static(well_ref, well_count, col_count):
        ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if isinstance(well_ref, list):
            return [
                ContainerType.humanize_static(well, well_count, col_count)
                for well in well_ref
            ]

        if not isinstance(well_ref, (int, str)):
            raise TypeError(
                "ContainerType.humanize(): Well reference given "
                "is not of type 'int' or 'str'."
            )
        try:
            well_ref = int(well_ref)
        except:
            raise TypeError(
                "ContainerType.humanize(): Well reference given"
                "is not parseable into 'int' format."
            )
        # Check bounds
        if well_ref >= well_count or well_ref < 0:
            raise ValueError(
                "ContainerType.humanize(): Well reference "
                "given exceeds container dimensions."
            )
        idx = ContainerType.robotize_static(well_ref, well_count, col_count)
        row, col = (idx // col_count, idx % col_count)
        if row >= len(ALPHABET):
            return ALPHABET[row // 26 - 1] + ALPHABET[row % 26] + str(col + 1)
        else:
            return ALPHABET[row] + str(col + 1)

    def humanize(self, well_ref):
        """
        Return the human readable form of a well index based on the well
        format of this ContainerType.

        Example Usage:

        .. code-block:: python

            >>> p = Protocol()
            >>> my_plate = p.ref("my_plate", cont_type="6-flat", discard=True)
            >>> my_plate.humanize(0)
            'A1'
            >>> my_plate.humanize(5)
            'B3'
            >>> my_plate.humanize('0')
            'A1'

        Parameters
        ----------
        well_ref : int, str, list[int or str]
            Well reference to be humanized in integer or string form.
            If string is provided, it has to be parseable into an int.
            Also accepts lists of int or str

        Returns
        -------
        well_ref : str
            Well index passed as human-readable form.

        Raises
        ------
        TypeError
            If well reference given is not an accepted type.
        ValueError
            If well reference given exceeds container dimensions.

        """
        return ContainerType.humanize_static(well_ref, self.well_count, self.col_count)

    def decompose(self, idx):
        """
        Return the (col, row) corresponding to the given well index.

        Parameters
        ----------
        idx : str or int
            Well index in either human-readable or integer form.

        Returns
        -------
        tuple
            tuple containing the column number and row number of the given
            well_ref.

        Raises
        ------
        TypeError
            Index given is not of the right parameter type

        """
        if not isinstance(idx, (int, str, Well)):
            raise TypeError("Well index given is not of type 'int' or " "'str'.")
        idx = self.robotize(idx)
        return (idx // self.col_count, idx % self.col_count)

    def row_count(self):
        """
        Return the number of rows of this ContainerType.

        """
        return self.well_count // self.col_count

    def sealable(self):
        """
        Return whether or not it has seal capability and seal types

        """
        has_enough = isinstance(self.seal_types, list) and len(self.seal_types) > 0
        return "seal" in self.capabilities and has_enough

    def coverable(self):
        """
        Return whether or not it has cover capability and cover types

        """
        has_enough = isinstance(self.cover_types, list) and len(self.cover_types) > 0
        return "cover" in self.capabilities and has_enough
