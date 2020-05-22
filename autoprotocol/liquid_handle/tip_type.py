"""
Generic tip type and device class mappings for LiquidHandleMethods

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details
"""
from collections import namedtuple

from ..util import parse_unit


class TipType(namedtuple("TipType", ["name", "volume"])):
    """
    The TipType class holds the properties of a TipType
    """

    def __new__(cls, name, volume):
        """
        Parameters
        ----------
        name : str
          Full name describing a TipType.
        volume : Unit
          The maximum capacity of the TipType.

        Returns
        -------
        TipType
            A tip type compatible with LiquidHandleMethods

        Raises
        ------
        TypeError
            if the name is not a str

        See Also
        --------
        :py:class: `autoprotocol.LiquidHandleMethod._get_tip_types`
        """
        if not isinstance(name, str):
            raise TypeError(f"TipType name {name} was not a str.")
        volume = parse_unit(volume, "uL")
        return super(TipType, cls).__new__(cls, name, volume)
