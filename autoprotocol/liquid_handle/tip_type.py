"""
Generic tip type and device class mappings for LiquidHandleMethods
"""
from collections import namedtuple
from autoprotocol.util import parse_unit


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

        Raises
        ------
        TypeError
            if the name is not a str
        """
        if not isinstance(name, str):
            raise TypeError("TipType name {} was not a str.".format(name))
        volume = parse_unit(volume, "uL")
        return super(TipType, cls).__new__(cls, name, volume)
