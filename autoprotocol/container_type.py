import re
import sys
from collections import namedtuple
from .container import Well
from .unit import Unit

if sys.version_info[0] >= 3:
    xrange = range
    basestring = str

'''
    :copyright: 2016 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


class ContainerType(namedtuple("ContainerType",
                               ["name", "is_tube", "well_count",
                                "well_depth_mm", "well_volume_ul",
                                "well_coating", "sterile", "cover_types",
                                "seal_types", "capabilities",
                                "shortname", "col_count", "dead_volume_ul",
                                "safe_min_volume_ul"])):
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
    cover_types: list
        List of valid covers associated with a ContainerType.
    seal_types: list
        List of valid seals associated with a ContainerType.
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
    safe_min_volume_ul : int
      Minimum volume of liquid to ensure adequate volume for liquid-handling
      aspiration from any given well of a ContainerType.

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
            >>> my_plate.robotize(["A1", "A2"])
            [0, 1]

        Parameters
        ----------
        well_ref : str, int, Well, list[str or int or Well]
            Well reference to be robotized in string, integer or Well object
            form. Also accepts lists of str, int or Well.

        Returns
        ----------
        well_ref : int, list
            Single or list of Well references passed as rowwise integer
            (left-to-right, top-to-bottom, starting at 0 = A1).

        Raises
        ------
        TypeError
            If well reference given is not an accepted type.
        ValueError
            If well reference given exceeds container dimensions.

        """
        if isinstance(well_ref, list):
            return [self.robotize(well) for well in well_ref]

        if not isinstance(well_ref, (basestring, int, Well)):
            raise TypeError("ContainerType.robotize(): Well reference (%s) "
                            "given is not of type 'str', 'int', or "
                            "'Well'." % well_ref)

        if isinstance(well_ref, Well):
            well_ref = well_ref.index
        well_ref = str(well_ref)
        m = re.match(r"([a-z])(\d+)$", well_ref, re.I)
        if m:
            row = ord(m.group(1).upper()) - ord('A')
            col = int(m.group(2)) - 1
            well_num = row * self.col_count + col
            # Check bounds
            if row >= self.row_count():
                raise ValueError("ContainerType.robotize(): Row given exceeds "
                                 "container dimensions.")
            if col >= self.col_count or col < 0:
                raise ValueError("ContainerType.robotize(): Col given exceeds "
                                 "container dimensions.")
            return well_num
        else:
            m = re.match(r"\d+$", well_ref)
            if m:
                well_num = int(m.group(0))
                # Check bounds
                if well_num >= self.well_count or well_num < 0:
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
        if isinstance(well_ref, list):
            return [self.humanize(well) for well in well_ref]

        if not isinstance(well_ref, (int, basestring)):
            raise TypeError("ContainerType.humanize(): Well reference given "
                            "is not of type 'int' or 'str'.")
        try:
            well_ref = int(well_ref)
        except:
            raise TypeError("ContainerType.humanize(): Well reference given"
                            "is not parseable into 'int' format.")
        # Check bounds
        if well_ref >= self.well_count or well_ref < 0:
            raise ValueError("ContainerType.humanize(): Well reference "
                             "given exceeds container dimensions.")
        row, col = self.decompose(well_ref)
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
            raise TypeError("Well index given is not of type 'int' or "
                            "'str'.")
        idx = self.robotize(idx)
        return (idx // self.col_count, idx % self.col_count)

    def row_count(self):
        """
        Return the number of rows of this ContainerType.

        """
        return self.well_count // self.col_count


_CONTAINER_TYPES = {
    "384-flat": ContainerType(
        name="384-well UV flat-bottom plate",
        well_count=384,
        well_depth_mm=None,
        well_volume_ul=Unit(90.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["standard", "universal"],
        seal_types=None,
        capabilities=["pipette", "spin", "absorbance",
                      "fluorescence", "luminescence",
                      "incubate", "gel_separate",
                      "gel_purify", "cover", "stamp",
                      "dispense"],
        shortname="384-flat",
        col_count=24,
        dead_volume_ul=Unit(5, "microliter"),
        safe_min_volume_ul=Unit(15, "microliter")
    ),
    "384-pcr": ContainerType(
        name="384-well PCR plate",
        well_count=384,
        well_depth_mm=None,
        well_volume_ul=Unit(50.0, "microliter"),
        well_coating=None,
        sterile=None,
        is_tube=False,
        cover_types=None,
        seal_types=["ultra-clear", "foil"],
        capabilities=["pipette", "spin", "thermocycle",
                      "incubate", "gel_separate",
                      "gel_purify",
                      "seal", "stamp", "dispense"],
        shortname="384-pcr",
        col_count=24,
        dead_volume_ul=Unit(2, "microliter"),
        safe_min_volume_ul=Unit(3, "microliter")
    ),
    "384-echo": ContainerType(
        name="384-well Echo plate",
        well_count=384,
        well_depth_mm=None,
        well_volume_ul=Unit(65.0, "microliter"),
        well_coating=None,
        sterile=None,
        is_tube=False,
        cover_types=["universal"],
        seal_types=["foil", "ultra-clear"],
        capabilities=["pipette", "seal", "spin",
                      "incubate", "stamp", "dispense",
                      "cover"],
        shortname="384-echo",
        col_count=24,
        dead_volume_ul=Unit(15, "microliter"),
        safe_min_volume_ul=Unit(15, "microliter")
    ),
    "384-flat-white-white-lv": ContainerType(
        name="384-well flat-bottom low volume plate",
        well_count=384,
        well_depth_mm=9.39,
        well_volume_ul=Unit(40.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["standard", "universal"],
        seal_types=None,
        capabilities=["absorbance", "cover", "dispense",
                      "fluorescence", "image_plate",
                      "incubate", "luminescence",
                      "pipette", "spin",
                      "stamp", "uncover"],
        shortname="384-flat-white-white-lv",
        col_count=24,
        dead_volume_ul=Unit(5, "microliter"),
        safe_min_volume_ul=Unit(15, "microliter")
    ),
    "384-flat-white-white-tc": ContainerType(
        name="384-well flat-bottom low flange plate",
        well_count=384,
        well_depth_mm=11.43,
        well_volume_ul=Unit(80.0, "microliter"),
        well_coating=None,
        sterile=True,
        is_tube=False,
        cover_types=["standard", "universal"],
        seal_types=None,
        capabilities=["absorbance", "cover", "dispense",
                      "fluorescence", "image_plate",
                      "incubate", "luminescence",
                      "pipette", "spin",
                      "stamp", "uncover"],
        shortname="384-flat-white-white-tc",
        col_count=24,
        dead_volume_ul=Unit(20, "microliter"),
        safe_min_volume_ul=Unit(30, "microliter")
    ),
    "384-flat-clear-clear": ContainerType(
        name="384-well fully clear high binding plate",
        well_count=384,
        well_depth_mm=11.43,
        well_volume_ul=Unit(80.0, "microliter"),
        well_coating="high bind",
        sterile=False,
        is_tube=False,
        cover_types=["standard", "universal", "low_evaporation"],
        seal_types=["ultra-clear", "foil"],
        capabilities=["incubate", "seal", "image_plate",
                      "stamp", "dispense", "spin",
                      "absorbance", "cover",
                      "fluorescence", "luminescence",
                      "pipette", "uncover"],
        shortname="384-flat-clear-clear",
        col_count=24,
        dead_volume_ul=Unit(5, "microliter"),
        safe_min_volume_ul=Unit(20, "microliter")
    ),
    "96-flat": ContainerType(
        name="96-well flat-bottom plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(340.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["low_evaporation", "standard", "universal"],
        seal_types=None,
        capabilities=["pipette", "spin", "absorbance",
                      "fluorescence", "luminescence",
                      "incubate", "gel_separate",
                      "gel_purify", "cover", "stamp",
                      "dispense"],
        shortname="96-flat",
        col_count=12,
        dead_volume_ul=Unit(25, "microliter"),
        safe_min_volume_ul=Unit(65, "microliter")
    ),
    "96-flat-uv": ContainerType(
        name="96-well flat-bottom UV transparent plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(340.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["low_evaporation", "standard", "universal"],
        seal_types=None,
        capabilities=["pipette", "spin", "absorbance",
                      "fluorescence", "luminescence",
                      "incubate", "gel_separate",
                      "gel_purify", "cover", "stamp",
                      "dispense"],
        shortname="96-flat-uv",
        col_count=12,
        dead_volume_ul=Unit(25, "microliter"),
        safe_min_volume_ul=Unit(65, "microliter")
    ),
    "96-pcr": ContainerType(
        name="96-well PCR plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(160.0, "microliter"),
        well_coating=None,
        sterile=None,
        is_tube=False,
        cover_types=None,
        seal_types=["ultra-clear", "foil"],
        capabilities=["pipette", "sangerseq", "spin",
                      "thermocycle", "incubate",
                      "gel_separate", "gel_purify",
                      "seal", "stamp", "dispense"],
        shortname="96-pcr",
        col_count=12,
        dead_volume_ul=Unit(3, "microliter"),
        safe_min_volume_ul=Unit(5, "microliter")
    ),
    "96-deep": ContainerType(
        name="96-well extended capacity plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(2000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["standard", "universal"],
        seal_types=None,
        capabilities=["pipette", "incubate",
                      "gel_separate", "gel_purify",
                      "cover", "stamp", "dispense"],
        shortname="96-deep",
        is_tube=False,
        col_count=12,
        dead_volume_ul=Unit(15, "microliter"),
        safe_min_volume_ul=Unit(30, "microliter")
    ),
    "96-v-kf": ContainerType(
        name="96-well v-bottom King Fisher plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(200.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["standard"],
        seal_types=None,
        capabilities=["pipette", "incubate",
                      "gel_separate", "mag_dry",
                      "mag_incubate", "mag_collect",
                      "mag_release", "mag_mix",
                      "cover", "stamp", "dispense"],
        shortname="96-v-kf",
        is_tube=False,
        col_count=12,
        dead_volume_ul=Unit(20, "microliter"),
        safe_min_volume_ul=Unit(20, "microliter")
    ),
    "96-deep-kf": ContainerType(
        name="96-well extended capacity King Fisher plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(1000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["standard"],
        seal_types=None,
        capabilities=["pipette", "incubate",
                      "gel_separate", "mag_dry",
                      "mag_incubate", "mag_collect",
                      "mag_release", "mag_mix",
                      "cover", "stamp", "dispense"],
        shortname="96-deep-kf",
        is_tube=False,
        col_count=12,
        dead_volume_ul=Unit(50, "microliter"),
        safe_min_volume_ul=Unit(50, "microliter")
    ),
    "24-deep": ContainerType(
        name="24-well extended capacity plate",
        well_count=24,
        well_depth_mm=None,
        well_volume_ul=Unit(10000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["universal"],
        seal_types=None,
        capabilities=["pipette", "incubate",
                      "gel_separate", "gel_purify",
                      "cover", "stamp", "dispense"],
        shortname="24-deep",
        is_tube=False,
        col_count=6,
        dead_volume_ul=Unit(15, "microliter"),
        safe_min_volume_ul=Unit(60, "microliter")
    ),
    "micro-2.0": ContainerType(
        name="2mL Microcentrifuge tube",
        well_count=1,
        well_depth_mm=None,
        well_volume_ul=Unit(2000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=None,
        seal_types=None,
        capabilities=["pipette", "gel_separate",
                      "gel_purify", "incubate", "spin"],
        shortname="micro-2.0",
        is_tube=True,
        col_count=1,
        dead_volume_ul=Unit(15, "microliter"),
        safe_min_volume_ul=Unit(40, "microliter")
    ),
    "micro-1.5": ContainerType(
        name="1.5mL Microcentrifuge tube",
        well_count=1,
        well_depth_mm=None,
        well_volume_ul=Unit(1500.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=None,
        seal_types=None,
        capabilities=["pipette", "gel_separate",
                      "gel_purify", "incubate", "spin"],
        shortname="micro-1.5",
        is_tube=True,
        col_count=1,
        dead_volume_ul=Unit(15, "microliter"),
        safe_min_volume_ul=Unit(20, "microliter")
    ),
    "6-flat": ContainerType(
        name="6-well cell culture plate",
        well_count=6,
        well_depth_mm=None,
        well_volume_ul=Unit(5000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["standard", "universal"],
        seal_types=None,
        capabilities=["cover", "incubate", "image_plate"],
        shortname="6-flat",
        is_tube=False,
        col_count=3,
        dead_volume_ul=Unit(400, "microliter"),
        safe_min_volume_ul=Unit(600, "microliter")
    ),
    "1-flat": ContainerType(
        name="1-well flat-bottom plate",
        well_count=1,
        well_depth_mm=None,
        well_volume_ul=Unit(80000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["universal"],
        seal_types=None,
        capabilities=["cover", "incubate"],
        shortname="1-flat",
        is_tube=False,
        col_count=1,
        dead_volume_ul=Unit(36000, "microliter"),
        safe_min_volume_ul=Unit(40000, "microliter")
    ),
    "6-flat-tc": ContainerType(
        name="6-well TC treated plate",
        well_count=6,
        well_depth_mm=None,
        well_volume_ul=Unit(5000.0, "microliter"),
        well_coating=None,
        sterile=False,
        cover_types=["standard", "universal"],
        seal_types=None,
        capabilities=["cover", "incubate", "image_plate"],
        shortname="6-flat-tc",
        is_tube=False,
        col_count=3,
        dead_volume_ul=Unit(400, "microliter"),
        safe_min_volume_ul=Unit(600, "microliter")
    ),
    "96-flat-clear-clear-tc": ContainerType(
        name="96-well flat-bottom TC treated plate",
        well_count=96,
        well_depth_mm=None,
        well_volume_ul=Unit(340.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["low_evaporation", "standard", "universal"],
        seal_types=None,
        capabilities=["pipette", "spin", "absorbance",
                      "fluorescence", "luminescence",
                      "incubate", "gel_separate",
                      "gel_purify", "cover", "stamp",
                      "dispense"],
        shortname="96-flat-clear-clear-tc",
        col_count=12,
        dead_volume_ul=Unit(25, "microliter"),
        safe_min_volume_ul=Unit(65, "microliter")),
    "384-v-clear-clear": ContainerType(
        name="384-well v-bottom polypropylene plate",
        well_count=384,
        well_depth_mm=None,
        well_volume_ul=Unit(120.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["universal", "standard"],
        seal_types=["ultra-clear", "foil"],
        capabilities=["incubate", "seal", "image_plate",
                      "stamp", "pipette", "dispense", "spin",
                      "mag_dry", "mag_incubate", "mag_collect",
                      "mag_release", "mag_mix", "absorbance",
                      "fluorescence", "luminescence", "cover",
                      "thermocycle"],
        shortname="384-v-clear-clear",
        col_count=24,
        dead_volume_ul=Unit(13, "microliter"),
        safe_min_volume_ul=Unit(18, "microliter")),
    "384-round-clear-clear": ContainerType(
        name="384-well round-bottom plate",
        well_count=384,
        well_depth_mm=None,
        well_volume_ul=Unit(70.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["universal", "standard"],
        seal_types=["ultra-clear", "foil"],
        capabilities=["incubate", "seal", "image_plate",
                      "stamp", "pipette", "dispense", "spin",
                      "mag_dry", "mag_incubate", "mag_collect",
                      "mag_release", "mag_mix", "absorbance",
                      "fluorescence", "luminescence", "cover",
                      "thermocycle"],
        shortname="384-round-clear-clear",
        col_count=24,
        dead_volume_ul=Unit(15, "microliter"),
        safe_min_volume_ul=Unit(20, "microliter")),
    "384-flat-white-white-nbs": ContainerType(
        name="384-well flat-bottom low flange polystyrene NBS plate",
        well_count=384,
        well_depth_mm=None,
        well_volume_ul=Unit(80.0, "microliter"),
        well_coating=None,
        sterile=False,
        is_tube=False,
        cover_types=["universal", "standard"],
        seal_types=["ultra-clear", "foil"],
        capabilities=["incubate", "seal", "image_plate",
                      "stamp", "pipette", "dispense", "spin",
                      "mag_dry", "mag_incubate", "mag_collect",
                      "mag_release", "mag_mix", "absorbance",
                      "fluorescence", "luminescence", "cover",
                      "thermocycle"],
        shortname="384-flat-white-white-nbs",
        col_count=24,
        dead_volume_ul=Unit(20, "microliter"),
        safe_min_volume_ul=Unit(25, "microliter"))
}
