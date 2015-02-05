import re
from collections import namedtuple
from .container import Well

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

class ContainerType(namedtuple("ContainerType",
                    ["name", "is_tube", "well_count",
                     "well_depth_mm", "well_volume_ul",
                     "well_coating", "sterile", "capabilities",
                     "shortname", "col_count","dead_volume_ul"])):

    """
    The ContainerType class holds the capabilities and properties of a
    particular container type.

    Parameters
    ----------
    name : str
      Full name describing a ContainerType.
    is_tube : bool
      Indicates whether a ContainerType is a tube (container with one well)
    well_count : int
      Number of wells a ContainerType contains.
    well_depth_mm : int
      Depth of well(s) contained in a ContainerType in millimeters.
    well_volume_ul : int
      Maximum volume of well(s) contained in a ContainerType in microliters.
    well_coating : str
    sterile : bool
      Indicates whether a ContainerType is sterile
    capabilities : list
      List of capabilities associated with a ContainerType.
    shortname : str
      Short name used to refer to a ContainerType.
    col_count : int
      Number of columns a ContainerType contains.
    dead_volume_ul : int
      Volume of liquid that cannot be aspirated from any given well of a
      ContainerType via liquid-handling

    """

    def robotize(self, well_ref):
        """
        Convert a well reference (int, "A1" or int-in-a-string "23") to a
        robot-friendly rowwise integer (left-to-right, top-to-bottom,
        starting at 0 = A1).

        Parameters
        ----------
        well_ref : str, int
          Well reference to be robotized.

        """
        if isinstance(well_ref, Well):
            well_ref = well_ref.index
        well_ref = str(well_ref)
        m = re.match("([a-z])(\d+)$", well_ref, re.I)
        # TODO(jeremy): check bounds
        if m:
            row = ord(m.group(1).upper()) - ord('A')
            col = int(m.group(2)) - 1
            return row * self.col_count + col
        else:
            m = re.match("\d+$", well_ref)
            if m:
                return int(m.group(0))
            else:
                raise Exception("Well must be in A1 format or be an integer")

    def humanize(self, well_ref):
        """
        Return the human readable form of an integer well index based on the
        well format of this ContainerType.

        Parameters
        ----------
        well_ref : int
          Integer well reference to be humanized

        """
        row, col = self.decompose(well_ref)
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[row] + str(col + 1)

    def decompose(self, idx):
        """Return the (col, row) corresponding to the given well index.

        Parameters
        ----------
        idx : int, str
          Well reference to be decomposed.
        """
        idx = self.robotize(idx)
        return (idx / self.col_count, idx % self.col_count)

    def row_count(self):
        """Return number of rows this ContainerType has.

        """
        return self.well_count / self.col_count


_CONTAINER_TYPES = {
    "384-flat": ContainerType(name="384-well UV flat-bottom plate",
                              well_count=384,
                              well_depth_mm=None,
                              well_volume_ul=112.0,
                              well_coating=None,
                              sterile=False,
                              is_tube=False,
                              capabilities=["spin", "incubate", "absorbance",
                                            "fluorescence", "luminescence"],
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
                             capabilities=["thermocycle", "spin", "incubate"],
                             shortname="384-pcr",
                             col_count=24,
                             dead_volume_ul=8),
    "96-flat": ContainerType(name="96-well flat-bottom plate",
                             well_count=96,
                             well_depth_mm=None,
                             well_volume_ul=360.0,
                             well_coating=None,
                             sterile=False,
                             is_tube=False,
                             capabilities=["spin", "incubate", "absorbance",
                                           "fluorescence", "luminescence",
                                           "gel_separate", "sangerseq"],
                             shortname="96-flat",
                             col_count=12,
                             dead_volume_ul=20),
    "96-pcr": ContainerType(name="96-well PCR plate",
                            well_count=96,
                            well_depth_mm=None,
                            well_volume_ul=160.0,
                            well_coating=None,
                            sterile=None,
                            is_tube=False,
                            capabilities=["thermocycle", "spin", "incubate",
                                          "sangerseq", "gel_separate"],
                            shortname="96-pcr",
                            col_count=12,
                            dead_volume_ul=15),
    "96-deep": ContainerType(name="96-well extended capacity plate",
                             well_count=96,
                             well_depth_mm=None,
                             well_volume_ul=2000.0,
                             well_coating=None,
                             sterile=False,
                             capabilities=["incubate", "pipette", "sangerseq",
                                           "spin", "gel_separate"],
                             shortname="96-deep",
                             is_tube=False,
                             col_count=12,
                             dead_volume_ul=15),
    "micro-2.0": ContainerType(name="2mL Microcentrifuge tube",
                               well_count=1,
                               well_depth_mm=None,
                               well_volume_ul=2000.0,
                               well_coating=None,
                               sterile=False,
                               capabilities=["spin", "incubate", "pipette",
                                             "sangerseq", "gel_separate"],
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
                               capabilities=["spin", "incubate", "pipette",
                                             "sangerseq", "gel_separate"],
                               shortname="micro-1.5",
                               is_tube=True,
                               col_count=1,
                               dead_volume_ul=15),
}
