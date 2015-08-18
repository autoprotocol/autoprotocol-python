import re
import sys
from collections import namedtuple
from .container import Well

if sys.version_info[0] >= 3:
    xrange = range
    basestring = str

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


class ContainerType(namedtuple("ContainerType",
                    ["name", "is_tube", "well_count",
                     "well_depth_mm", "well_volume_ul",
                     "well_coating", "sterile", "capabilities",
                     "shortname", "col_count", "dead_volume_ul"])):

    """
    The ContainerType class holds the capabilities and properties of a
    particular container type.

    Parameters
    ----------
    name : str
      Full name describing a ContainerType.
    is_tube : bool
      Indicates whether a ContainerType is a tube (container with one well).
    well_count : int
      Number of wells a ContainerType contains.
    well_depth_mm : int
      Depth of well(s) contained in a ContainerType in millimeters.
    well_volume_ul : int
      Maximum volume of well(s) contained in a ContainerType in microliters.
    well_coating : str
      Coating of well(s) in container (ex. collagen).
    sterile : bool
      Indicates whether a ContainerType is sterile.
    capabilities : list
      List of capabilities associated with a ContainerType (ex. ["spin",
        "incubate"]).
    shortname : str
      Short name used to refer to a ContainerType.
    col_count : int
      Number of columns a ContainerType contains.
    dead_volume_ul : int
      Volume of liquid that cannot be aspirated from any given well of a
      ContainerType via liquid-handling.

    """

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

        Parameters
        ----------
        well_ref : str, int, Well
          Well reference to be robotized in string, integer or Well object
          form.

        Returns
        ----------
        well_ref : int
          Well reference passed as rowwise integer (left-to-right,
          top-to-bottom, starting at 0 = A1).

        Raises
        ------
        ValueError
            If well reference given exceeds container dimensions.

        """
        if not isinstance(well_ref, (basestring, int, Well)):
            raise TypeError("ContainerType.robotize(): Well reference given "
                            "is not of type 'str', 'int', or 'Well'.")

        if isinstance(well_ref, Well):
            well_ref = well_ref.index
        well_ref = str(well_ref)
        m = re.match("([a-z])(\d+)$", well_ref, re.I)
        if m:
            row = ord(m.group(1).upper()) - ord('A')
            col = int(m.group(2)) - 1
            well_num = row * self.col_count + col
            # Check bounds
            if row > self.row_count():
                raise ValueError("ContainerType.robotize(): Row given exceeds "
                                 "container dimensions.")
            if col > self.col_count or col < 0:
                raise ValueError("ContainerType.robotize(): Col given exceeds "
                                 "container dimensions.")
            if well_num > self.well_count:
                raise ValueError("ContainerType.robotize(): Well given "
                                 "exceeds container dimensions.")
            return well_num
        else:
            m = re.match("\d+$", well_ref)
            if m:
                well_num = int(m.group(0))
                # Check bounds
                if well_num > self.well_count or well_num < 0:
                    raise ValueError("ContainerType.robotize(): Well number "
                                     "given exceeds container dimensions.")
                return well_num
            else:
                raise ValueError("ContainerType.robotize(): Well must be in "
                                 "'A1' format or be an integer.")

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

        Parameters
        ----------
        well_ref : int
          Well reference to be humanized in integer form.

        Returns
        -------
        well_ref : str
            Well index passed as human-readable form.

        Raises
        ------
        ValueError
            If well reference given exceeds container dimensions.

        """
        if not isinstance(well_ref, int):
            raise TypeError("ContainerType.humanize(): Well reference given "
                            "is not of type 'int'.")
        row, col = self.decompose(well_ref)
        # Check bounds
        if well_ref > self.well_count or well_ref < 0:
                raise ValueError("ContainerType.humanize(): Well reference "
                                 "given exceeds container dimensions.")
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[row] + str(col + 1)

    def decompose(self, idx):
        """
        Return the (col, row) corresponding to the given well index.

        Parameters
        ----------
        well_ref : str, int
            Well index in either human-readable or integer form.

        Returns
        -------
        well_ref : tuple
            tuple containing the column number and row number of the given
            well_ref.

        """
        if not isinstance(idx, (int, basestring, Well)):
            raise TypeError("Well index given is not of type 'int' or \
                            'str'.")
        idx = self.robotize(idx)
        return (idx // self.col_count, idx % self.col_count)

    def row_count(self):
        """
        Return the number of rows of this ContainerType.

        """
        return self.well_count // self.col_count


_CONTAINER_TYPES = {
    "384-flat": ContainerType(name="384-well UV flat-bottom plate",
                              well_count=384,
                              well_depth_mm=None,
                              well_volume_ul=112.0,
                              well_coating=None,
                              sterile=False,
                              is_tube=False,
                              capabilities=[],
                              shortname="384-flat",
                              col_count=24,
                              dead_volume_ul=12),
    "384-pcr": ContainerType(name="384-well PCR plate",
                             well_count=384,
                             well_depth_mm=None,
                             well_volume_ul=50.0,
                             well_coating=None,
                             sterile=None,
                             is_tube=False,
                             capabilities=[],
                             shortname="384-pcr",
                             col_count=24,
                             dead_volume_ul=8),
    "384-echo": ContainerType(name="384-well Echo plate",
                              well_count=384,
                              well_depth_mm=None,
                              well_volume_ul=65.0,
                              well_coating=None,
                              sterile=None,
                              is_tube=False,
                              capabilities=[],
                              shortname="384-echo",
                              col_count=24,
                              dead_volume_ul=5),
    "96-flat": ContainerType(name="96-well flat-bottom plate",
                             well_count=96,
                             well_depth_mm=None,
                             well_volume_ul=340.0,
                             well_coating=None,
                             sterile=False,
                             is_tube=False,
                             capabilities=[],
                             shortname="96-flat",
                             col_count=12,
                             dead_volume_ul=25),
    "96-flat-uv": ContainerType(name="96-well flat-bottom UV transparent \
                                plate",
                                well_count=96,
                                well_depth_mm=None,
                                well_volume_ul=340.0,
                                well_coating=None,
                                sterile=False,
                                is_tube=False,
                                capabilities=[],
                                shortname="96-flat-uv",
                                col_count=12,
                                dead_volume_ul=25),
    "96-pcr": ContainerType(name="96-well PCR plate",
                            well_count=96,
                            well_depth_mm=None,
                            well_volume_ul=160.0,
                            well_coating=None,
                            sterile=None,
                            is_tube=False,
                            capabilities=[],
                            shortname="96-pcr",
                            col_count=12,
                            dead_volume_ul=15),
    "96-deep": ContainerType(name="96-well extended capacity plate",
                             well_count=96,
                             well_depth_mm=None,
                             well_volume_ul=2000.0,
                             well_coating=None,
                             sterile=False,
                             capabilities=[],
                             shortname="96-deep",
                             is_tube=False,
                             col_count=12,
                             dead_volume_ul=15),
    "24-deep": ContainerType(name="24-well extended capacity plate",
                             well_count=24,
                             well_depth_mm=None,
                             well_volume_ul=10000.0,
                             well_coating=None,
                             sterile=False,
                             capabilities=[],
                             shortname="24-deep",
                             is_tube=False,
                             col_count=6,
                             dead_volume_ul=15),
    "micro-2.0": ContainerType(name="2mL Microcentrifuge tube",
                               well_count=1,
                               well_depth_mm=None,
                               well_volume_ul=2000.0,
                               well_coating=None,
                               sterile=False,
                               capabilities=[],
                               shortname="micro-2.0",
                               is_tube=True,
                               col_count=1,
                               dead_volume_ul=15),
    "micro-1.5": ContainerType(name="1.5mL Microcentrifuge tube",
                               well_count=1,
                               well_depth_mm=None,
                               well_volume_ul=1500.0,
                               well_coating=None,
                               sterile=False,
                               capabilities=[],
                               shortname="micro-1.5",
                               is_tube=True,
                               col_count=1,
                               dead_volume_ul=15),
    "6-flat": ContainerType(name="6-well cell culture plate",
                            well_count=6,
                            well_depth_mm=None,
                            well_volume_ul=1500.0,
                            well_coating=None,
                            sterile=False,
                            capabilities=[],
                            shortname="6-flat",
                            is_tube=False,
                            col_count=3,
                            dead_volume_ul=15),
    "1-flat": ContainerType(name="1-well flat-bottom plate",
                            well_count=1,
                            well_depth_mm=None,
                            well_volume_ul=80000.0,
                            well_coating=None,
                            sterile=False,
                            capabilities=[],
                            shortname="1-flat",
                            is_tube=False,
                            col_count=1,
                            dead_volume_ul=36000),
}
