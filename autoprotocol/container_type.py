import re
from collections import namedtuple
from .container import Well


class ContainerType(namedtuple("ContainerType",
                    ["name", "is_tube", "well_count", "well_type",
                     "well_depth_mm", "well_volume_ul",
                     "well_coating", "sterile", "capabilities",
                     "shortname", "col_count"])):
    """The ContainerType class holds the capabilities and properties of a
    particular container type.
    """

    def robotize(self, well_ref):
        """
        Convert a well reference (int, "A1" or int-in-a-string "23") to a
        robot-friendly rowwise integer (left-to-right, top-to-bottom,
        starting at 0 = A1).
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
        row, col = self.decompose(well_ref)
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[row] + str(col + 1)

    def decompose(self, idx):
        """
        Return the (col, row) corresponding to the given idx.
        """
        idx = self.robotize(idx)
        return (idx / self.col_count, idx % self.col_count)

    def row_count(self):
        return self.well_count / self.col_count


_CONTAINER_TYPES = {
    "384-flat": ContainerType(name="384-well UV flat-bottom plate",
                              well_count=384,
                              well_type=None,
                              well_depth_mm=None,
                              well_volume_ul=112.0,
                              well_coating=None,
                              sterile=False,
                              is_tube=False,
                              capabilities=["spin", "incubate", "absorbance",
                                            "fluorescence", "luminescence"],
                              shortname="384-flat",
                              col_count=24),
    "384-pcr": ContainerType(name="384-well PCR plate",
                             well_count=384,
                             well_type=None,
                             well_depth_mm=None,
                             well_volume_ul=50.0,
                             well_coating=None,
                             sterile=None,
                             is_tube=False,
                             capabilities=["thermocycle", "spin", "incubate"],
                             shortname="384-pcr",
                             col_count=24),
    "96-flat": ContainerType(name="96-well flat-bottom plate",
                             well_count=96,
                             well_type=None,
                             well_depth_mm=None,
                             well_volume_ul=360.0,
                             well_coating=None,
                             sterile=False,
                             is_tube=False,
                             capabilities=["spin", "incubate", "absorbance",
                                           "fluorescence", "luminescence"],
                             shortname="96-flat",
                             col_count=12),
    "96-pcr": ContainerType(name="96-well PCR plate",
                            well_count=96,
                            well_type=None,
                            well_depth_mm=None,
                            well_volume_ul=None,
                            well_coating=None,
                            sterile=None,
                            is_tube=False,
                            capabilities=["thermocycle", "spin", "incubate"],
                            shortname="96-pcr",
                            col_count=12),
    "96-deep": ContainerType(name="96-well extended capacity plate",
                             well_count=96,
                             well_type=None,
                             well_depth_mm=None,
                             well_volume_ul=2000.0,
                             well_coating=None,
                             sterile=False,
                             capabilities=["incubate"],
                             shortname="96-deep",
                             is_tube=False,
                             col_count=12),
    "micro-2.0": ContainerType(name="2mL Microcentrifuge tube",
                               well_count=1,
                               well_type=None,
                               well_depth_mm=None,
                               well_volume_ul=2000.0,
                               well_coating=None,
                               sterile=False,
                               capabilities=["spin", "incubate"],
                               shortname="micro-2.0",
                               is_tube=True,
                               col_count=1),
    "micro-1.5": ContainerType(name="1.5mL Microcentrifuge tube",
                               well_count=1,
                               well_type=None,
                               well_depth_mm=None,
                               well_volume_ul=1500.0,
                               well_coating=None,
                               sterile=False,
                               capabilities=["spin", "incubate"],
                               shortname="micro-1.5",
                               is_tube=True,
                               col_count=1),
}
