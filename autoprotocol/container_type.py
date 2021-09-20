"""
Container-type object and associated functions

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""
import re

from collections import namedtuple

from .container import Well
from .unit import Unit


class ContainerType(
    namedtuple(
        "ContainerType",
        [
            "name",
            "is_tube",
            "well_count",
            "well_depth_mm",
            "well_volume_ul",
            "well_coating",
            "sterile",
            "cover_types",
            "seal_types",
            "capabilities",
            "shortname",
            "col_count",
            "dead_volume_ul",
            "safe_min_volume_ul",
            "true_max_vol_ul",
            "vendor",
            "cat_no",
            "prioritize_seal_or_cover",
        ],
    )
):
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
    well_depth_mm : float
      Depth of well(s) contained in a ContainerType in millimeters.
    well_volume_ul : Unit
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
    dead_volume_ul : Unit
      Volume of liquid that cannot be aspirated from any given well of a
      ContainerType via liquid-handling.
    safe_min_volume_ul : Unit
      Minimum volume of liquid to ensure adequate volume for liquid-handling
      aspiration from any given well of a ContainerType.
    true_max_vol_ul : Unit, optional
      Maximum volume of well(s) in microliters, often same value as
      well_volume_ul (maximum working volume), however, some ContainerType(s)
      can have a different value corresponding to a true maximum volume
      of a well (ex. echo compatible containers)
    vendor: str, optional
      ContainerType commercial vendor, if available.
    cat_no: str, optional
      ContainerType vendor catalog number, if available.
    prioritize_seal_or_cover: str, optional
        "seal" or "cover", determines whether to prioritize sealing or covering
        defaults to "seal"
    """

    def __new__(
        cls,
        name,
        is_tube,
        well_count,
        well_depth_mm,
        well_volume_ul,
        well_coating,
        sterile,
        cover_types,
        seal_types,
        capabilities,
        shortname,
        col_count,
        dead_volume_ul,
        safe_min_volume_ul,
        true_max_vol_ul=None,
        vendor=None,
        cat_no=None,
        prioritize_seal_or_cover="seal",
    ):
        true_max_vol_ul = true_max_vol_ul or well_volume_ul
        assert true_max_vol_ul >= well_volume_ul, (
            f"{name} does not contain valid true_max_vol_ul: "
            f"{true_max_vol_ul} and well_volume_ul {well_volume_ul}"
        )
        return super(ContainerType, cls).__new__(
            cls,
            name,
            is_tube,
            well_count,
            well_depth_mm,
            well_volume_ul,
            well_coating,
            sterile,
            cover_types,
            seal_types,
            capabilities,
            shortname,
            col_count,
            dead_volume_ul,
            safe_min_volume_ul,
            true_max_vol_ul,
            vendor,
            cat_no,
            prioritize_seal_or_cover,
        )

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


#:
FLAT384 = ContainerType(
    name="384-well UV flat-bottom plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(90.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["standard", "universal"],
    seal_types=["ultra-clear", "foil"],
    prioritize_seal_or_cover="cover",
    capabilities=[
        "liquid_handle",
        "spin",
        "absorbance",
        "fluorescence",
        "luminescence",
        "incubate",
        "gel_separate",
        "gel_purify",
        "cover",
        "dispense",
        "seal",
    ],
    shortname="384-flat",
    col_count=24,
    dead_volume_ul=Unit(7, "microliter"),
    safe_min_volume_ul=Unit(15, "microliter"),
    vendor="Corning",
    cat_no="3706",
)


#:
PCR384 = ContainerType(
    name="384-well PCR plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(40.0, "microliter"),
    well_coating=None,
    sterile=None,
    is_tube=False,
    cover_types=None,
    seal_types=["ultra-clear", "foil"],
    capabilities=[
        "liquid_handle",
        "spin",
        "thermocycle",
        "incubate",
        "gel_separate",
        "gel_purify",
        "seal",
        "dispense",
    ],
    shortname="384-pcr",
    col_count=24,
    dead_volume_ul=Unit(2, "microliter"),
    safe_min_volume_ul=Unit(3, "microliter"),
    vendor="Eppendorf",
    cat_no="951020539",
)

#:
ECHO384 = ContainerType(
    # Compatible with Labcyte Echo 520, 525 and 55x
    name="384-well Echo plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(65.0, "microliter"),
    well_coating=None,
    sterile=None,
    is_tube=False,
    cover_types=["universal"],
    seal_types=["foil", "ultra-clear"],
    capabilities=["liquid_handle", "seal", "spin", "incubate", "dispense", "cover"],
    shortname="384-echo",
    col_count=24,
    dead_volume_ul=Unit(15, "microliter"),
    safe_min_volume_ul=Unit(15, "microliter"),
    true_max_vol_ul=Unit(135, "microliter"),
    vendor="Labcyte",
    cat_no="PP-0200",
)

#:
FLAT384WHITELV = ContainerType(
    name="384-well flat-bottom low volume plate",
    well_count=384,
    well_depth_mm=9.39,
    well_volume_ul=Unit(40.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["standard", "universal"],
    seal_types=None,
    capabilities=[
        "absorbance",
        "cover",
        "dispense",
        "fluorescence",
        "image_plate",
        "incubate",
        "luminescence",
        "liquid_handle",
        "spin",
        "uncover",
    ],
    shortname="384-flat-white-white-lv",
    col_count=24,
    dead_volume_ul=Unit(5, "microliter"),
    safe_min_volume_ul=Unit(15, "microliter"),
    vendor="Corning",
    cat_no="3824",
)

#:
FLAT384WHITETC = ContainerType(
    name="384-well flat-bottom low flange plate",
    well_count=384,
    well_depth_mm=11.43,
    well_volume_ul=Unit(80.0, "microliter"),
    well_coating=None,
    sterile=True,
    is_tube=False,
    cover_types=["standard", "universal"],
    seal_types=None,
    capabilities=[
        "absorbance",
        "cover",
        "dispense",
        "fluorescence",
        "image_plate",
        "incubate",
        "luminescence",
        "liquid_handle",
        "spin",
        "uncover",
    ],
    shortname="384-flat-white-white-tc",
    col_count=24,
    dead_volume_ul=Unit(20, "microliter"),
    safe_min_volume_ul=Unit(30, "microliter"),
    vendor="Corning",
    cat_no="3570",
)

#:
FLAT384CLEAR = ContainerType(
    name="384-well fully clear high binding plate",
    well_count=384,
    well_depth_mm=11.43,
    well_volume_ul=Unit(80.0, "microliter"),
    well_coating="high bind",
    sterile=False,
    is_tube=False,
    cover_types=["standard", "universal", "low_evaporation"],
    seal_types=["ultra-clear", "foil"],
    capabilities=[
        "incubate",
        "seal",
        "image_plate",
        "dispense",
        "spin",
        "absorbance",
        "cover",
        "fluorescence",
        "luminescence",
        "liquid_handle",
        "uncover",
    ],
    shortname="384-flat-clear-clear",
    col_count=24,
    dead_volume_ul=Unit(5, "microliter"),
    safe_min_volume_ul=Unit(20, "microliter"),
    vendor="Corning",
    cat_no="3700",
)

#:
FLAT96 = ContainerType(
    name="96-well flat-bottom plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(340.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["low_evaporation", "standard", "universal"],
    seal_types=None,
    capabilities=[
        "liquid_handle",
        "spin",
        "absorbance",
        "fluorescence",
        "luminescence",
        "incubate",
        "gel_separate",
        "gel_purify",
        "cover",
        "dispense",
    ],
    shortname="96-flat",
    col_count=12,
    dead_volume_ul=Unit(25, "microliter"),
    safe_min_volume_ul=Unit(65, "microliter"),
    vendor="Corning",
    cat_no="3632",
)

#:
FLAT96UV = ContainerType(
    name="96-well flat-bottom UV transparent plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(340.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["low_evaporation", "standard", "universal"],
    seal_types=None,
    capabilities=[
        "liquid_handle",
        "spin",
        "absorbance",
        "fluorescence",
        "luminescence",
        "incubate",
        "gel_separate",
        "gel_purify",
        "cover",
        "dispense",
    ],
    shortname="96-flat-uv",
    col_count=12,
    dead_volume_ul=Unit(25, "microliter"),
    safe_min_volume_ul=Unit(65, "microliter"),
    vendor="Corning",
    cat_no="3635",
)

#:
PCR96 = ContainerType(
    name="96-well PCR plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(160.0, "microliter"),
    well_coating=None,
    sterile=None,
    is_tube=False,
    cover_types=None,
    seal_types=["ultra-clear", "foil"],
    capabilities=[
        "liquid_handle",
        "sangerseq",
        "spin",
        "thermocycle",
        "incubate",
        "gel_separate",
        "gel_purify",
        "seal",
        "dispense",
    ],
    shortname="96-pcr",
    col_count=12,
    dead_volume_ul=Unit(3, "microliter"),
    safe_min_volume_ul=Unit(5, "microliter"),
    vendor="Eppendorf",
    cat_no="951020619",
)

#:
DEEP96 = ContainerType(
    name="96-well extended capacity plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(2000.0, "microliter"),
    well_coating=None,
    sterile=False,
    cover_types=["standard", "universal"],
    seal_types=["breathable"],
    prioritize_seal_or_cover="cover",
    capabilities=[
        "liquid_handle",
        "incubate",
        "gel_separate",
        "gel_purify",
        "cover",
        "dispense",
        "seal",
    ],
    shortname="96-deep",
    is_tube=False,
    col_count=12,
    dead_volume_ul=Unit(5, "microliter"),
    safe_min_volume_ul=Unit(30, "microliter"),
    vendor="Corning",
    cat_no="3961",
)

#:
V96KF = ContainerType(
    name="96-well v-bottom King Fisher plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(200.0, "microliter"),
    well_coating=None,
    sterile=False,
    cover_types=["standard"],
    seal_types=None,
    capabilities=[
        "liquid_handle",
        "incubate",
        "gel_separate",
        "mag_dry",
        "mag_incubate",
        "mag_collect",
        "mag_release",
        "mag_mix",
        "cover",
        "dispense",
    ],
    shortname="96-v-kf",
    is_tube=False,
    col_count=12,
    dead_volume_ul=Unit(20, "microliter"),
    safe_min_volume_ul=Unit(20, "microliter"),
    vendor="Fisher",
    cat_no="22-387-030",
)

#:
DEEP96KF = ContainerType(
    name="96-well extended capacity King Fisher plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(1000.0, "microliter"),
    well_coating=None,
    sterile=False,
    cover_types=["standard"],
    seal_types=None,
    capabilities=[
        "liquid_handle",
        "incubate",
        "gel_separate",
        "mag_dry",
        "mag_incubate",
        "mag_collect",
        "mag_release",
        "mag_mix",
        "cover",
        "dispense",
    ],
    shortname="96-deep-kf",
    is_tube=False,
    col_count=12,
    dead_volume_ul=Unit(50, "microliter"),
    safe_min_volume_ul=Unit(50, "microliter"),
    vendor="Fisher",
    cat_no="22-387-031",
)

#:
V96CC = ContainerType(
    name="96-well cell culture multiple well plate, V bottom",
    well_count=96,
    well_depth_mm=10.668,
    well_volume_ul=Unit(200.0, "microliter"),
    well_coating=None,
    sterile=True,
    is_tube=False,
    cover_types=["standard", "universal", "low_evaporation", "ultra-clear", "foil"],
    seal_types=None,
    capabilities=[
        "dispense",
        "spin",
        "seal",
        "unseal",
        "liquid_handle",
        "cover",
        "echo_dest",
        "spectrophotometry",
        "image_plate",
        "incubate",
        "uncover",
        "dispense-destination",
        "envision",
        "absorbance",
        "fluorescence",
    ],
    shortname="96-well-v-bottom",
    col_count=12,
    dead_volume_ul=Unit(75.0, "microliter"),
    safe_min_volume_ul=Unit(5.0, "microliter"),
    true_max_vol_ul=Unit(320.0, "microliter"),
    vendor="Corning",
    cat_no="3894",
)

#:
DEEP24 = ContainerType(
    name="24-well extended capacity plate",
    well_count=24,
    well_depth_mm=None,
    well_volume_ul=Unit(10000.0, "microliter"),
    well_coating=None,
    sterile=False,
    cover_types=None,
    seal_types=["foil", "breathable"],
    capabilities=[
        "liquid_handle",
        "incubate",
        "gel_separate",
        "gel_purify",
        "dispense",
        "seal",
    ],
    shortname="24-deep",
    is_tube=False,
    col_count=6,
    dead_volume_ul=Unit(15, "microliter"),
    safe_min_volume_ul=Unit(60, "microliter"),
    vendor="E&K Scientific",
    cat_no="EK-2053-S",
)

#:
MICRO2 = ContainerType(
    name="2mL Microcentrifuge tube",
    well_count=1,
    well_depth_mm=None,
    well_volume_ul=Unit(2000.0, "microliter"),
    well_coating=None,
    sterile=False,
    cover_types=None,
    seal_types=None,
    capabilities=["liquid_handle", "gel_separate", "gel_purify", "incubate", "spin"],
    shortname="micro-2.0",
    is_tube=True,
    col_count=1,
    dead_volume_ul=Unit(5, "microliter"),
    safe_min_volume_ul=Unit(40, "microliter"),
    vendor="E&K Scientific",
    cat_no="280200",
)

#:
MICRO15 = ContainerType(
    name="1.5mL Microcentrifuge tube",
    well_count=1,
    well_depth_mm=None,
    well_volume_ul=Unit(1500.0, "microliter"),
    well_coating=None,
    sterile=False,
    cover_types=None,
    seal_types=None,
    capabilities=["liquid_handle", "gel_separate", "gel_purify", "incubate", "spin"],
    shortname="micro-1.5",
    is_tube=True,
    col_count=1,
    dead_volume_ul=Unit(20, "microliter"),
    safe_min_volume_ul=Unit(20, "microliter"),
    vendor="USA Scientific",
    cat_no="1615-5500",
)

#:
FLAT6 = ContainerType(
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
    safe_min_volume_ul=Unit(600, "microliter"),
    vendor="Eppendorf",
    cat_no="30720016",
)

#:
FLAT1 = ContainerType(
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
    safe_min_volume_ul=Unit(40000, "microliter"),
    vendor="Fisher",
    cat_no="267060",
)

#:
FLAT6TC = ContainerType(
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
    safe_min_volume_ul=Unit(600, "microliter"),
    vendor="Eppendorf",
    cat_no="30720113",
)

#:
RESSW96HP = ContainerType(
    name="96-well singlewell highprofile reservoir",
    well_count=1,
    well_depth_mm=None,
    well_volume_ul=Unit(170.0, "milliliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["universal"],
    seal_types=None,
    capabilities=["liquid_handle", "incubate", "cover", "dispense", "liquid_handle"],
    shortname="res-sw96-hp",
    col_count=1,
    dead_volume_ul=Unit(25, "milliliter"),
    safe_min_volume_ul=Unit(30, "milliliter"),
    true_max_vol_ul=Unit(280.0, "milliliter"),
    vendor="Axygen",
    cat_no="res-sw96-hp",
)

#:
RESMW8HP = ContainerType(
    name="8-row multiwell highprofile reservoir",
    well_count=8,
    well_depth_mm=None,
    well_volume_ul=Unit(24.0, "milliliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["universal"],
    seal_types=None,
    capabilities=["liquid_handle", "incubate", "cover", "dispense", "liquid_handle"],
    shortname="res-mw8-hp",
    col_count=1,
    dead_volume_ul=Unit(2.5, "milliliter"),
    safe_min_volume_ul=Unit(5, "milliliter"),
    true_max_vol_ul=Unit(32.0, "milliliter"),
    vendor="Axygen",
    cat_no="res-mw8-hp",
)

#:
RESMW12HP = ContainerType(
    name="12-column multiwell highprofile reservoir",
    well_count=12,
    well_depth_mm=None,
    well_volume_ul=Unit(15.75, "milliliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["universal"],
    seal_types=None,
    capabilities=["liquid_handle", "incubate", "cover", "dispense", "liquid_handle"],
    shortname="res-mw12-hp",
    col_count=12,
    dead_volume_ul=Unit(1.8, "milliliter"),
    safe_min_volume_ul=Unit(5, "milliliter"),
    true_max_vol_ul=Unit(21.0, "milliliter"),
    vendor="Axygen",
    cat_no="res-mw12-hp",
)

#:
FLAT96CLEARTC = ContainerType(
    name="96-well flat-bottom TC treated plate",
    well_count=96,
    well_depth_mm=None,
    well_volume_ul=Unit(340.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["low_evaporation", "standard", "universal"],
    seal_types=None,
    capabilities=[
        "liquid_handle",
        "spin",
        "absorbance",
        "fluorescence",
        "luminescence",
        "incubate",
        "gel_separate",
        "gel_purify",
        "cover",
        "dispense",
    ],
    shortname="96-flat-clear-clear-tc",
    col_count=12,
    dead_volume_ul=Unit(25, "microliter"),
    safe_min_volume_ul=Unit(65, "microliter"),
    vendor="Eppendorf",
    cat_no="0030730119",
)

#:
V384CLEAR = ContainerType(
    name="384-well v-bottom polypropylene plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(120.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["universal", "standard"],
    seal_types=["ultra-clear", "foil"],
    capabilities=[
        "incubate",
        "seal",
        "image_plate",
        "liquid_handle",
        "dispense",
        "spin",
        "mag_dry",
        "mag_incubate",
        "mag_collect",
        "mag_release",
        "mag_mix",
        "absorbance",
        "fluorescence",
        "luminescence",
        "cover",
        "thermocycle",
    ],
    shortname="384-v-clear-clear",
    col_count=24,
    dead_volume_ul=Unit(13, "microliter"),
    safe_min_volume_ul=Unit(18, "microliter"),
    vendor="Greiner",
    cat_no="781280",
)

#:
ROUND384CLEAR = ContainerType(
    name="384-well round-bottom plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(70.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["universal", "standard"],
    seal_types=["ultra-clear", "foil"],
    capabilities=[
        "incubate",
        "seal",
        "image_plate",
        "liquid_handle",
        "dispense",
        "spin",
        "mag_dry",
        "mag_incubate",
        "mag_collect",
        "mag_release",
        "mag_mix",
        "absorbance",
        "fluorescence",
        "luminescence",
        "cover",
        "thermocycle",
    ],
    shortname="384-round-clear-clear",
    col_count=24,
    dead_volume_ul=Unit(15, "microliter"),
    safe_min_volume_ul=Unit(20, "microliter"),
    vendor="Corning",
    cat_no="3657",
)

#:
RESSW384LP = ContainerType(
    name="384-well singlewell lowprofile reservoir",
    well_count=1,
    well_depth_mm=None,
    well_volume_ul=Unit(35, "milliliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["universal"],
    seal_types=None,
    capabilities=[
        "liquid_handle",
        "incubate",
        "cover",
        "dispense",
        "liquid_handle",
        "sbs384_compatible",
    ],
    shortname="res-sw384-lp",
    col_count=1,
    dead_volume_ul=Unit(10, "milliliter"),
    safe_min_volume_ul=Unit(30, "milliliter"),
    true_max_vol_ul=Unit(92, "milliliter"),
    vendor="Axygen",
    cat_no="res-sw384-lp",
)

#:
ECHO384LDV = ContainerType(
    # Compatible with Labcyte Echo 520 and 55x only
    name="384-well Echo low dead volume plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(14.0, "microliter"),
    well_coating=None,
    sterile=None,
    is_tube=False,
    cover_types=["universal"],
    seal_types=["foil", "ultra-clear"],
    capabilities=["liquid_handle", "seal", "spin", "incubate", "dispense", "cover"],
    shortname="384-echo-ldv",
    col_count=24,
    dead_volume_ul=Unit(2.5, "microliter"),
    safe_min_volume_ul=Unit(2.5, "microliter"),
    vendor="Labcyte",
    cat_no="LP-0200",
)

#:
ECHO384LDVPLUS = ContainerType(
    # Compatible with Labcyte Echo 525 only
    name="384-well Echo low dead volume plus plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(14.0, "microliter"),
    well_coating="PureCoat Amine Surface",
    sterile=None,
    is_tube=False,
    cover_types=["universal"],
    seal_types=["foil", "ultra-clear"],
    capabilities=["liquid_handle", "seal", "spin", "incubate", "dispense", "cover"],
    shortname="384-echo-ldv-plus",
    col_count=24,
    dead_volume_ul=Unit(4.5, "microliter"),
    safe_min_volume_ul=Unit(4.5, "microliter"),
    vendor="Labcyte",
    cat_no="LPL-0200",
)

#:
FLAT384WHITECLEAR = ContainerType(
    name="384-well flat-bottom polystyrene plate",
    well_count=384,
    well_depth_mm=None,
    well_volume_ul=Unit(90.0, "microliter"),
    well_coating=None,
    sterile=False,
    is_tube=False,
    cover_types=["standard", "universal"],
    seal_types=["breathable", "ultra-clear"],
    capabilities=[
        "liquid_handle",
        "spin",
        "absorbance",
        "fluorescence",
        "luminescence",
        "incubate",
        "gel_separate",
        "gel_purify",
        "cover",
        "dispense",
        "seal",
    ],
    shortname="384-flat-white-clear",
    col_count=24,
    dead_volume_ul=Unit(7, "microliter"),
    safe_min_volume_ul=Unit(15, "microliter"),
    vendor="Corning",
    cat_no="3763",
)

#:
FALCON96UBOTTOM = ContainerType(
    name="Falcon 96-Well, Cell Culture-Treated, U-Shaped-Bottom Microplate",
    shortname="96-ubottom-clear-tc",
    is_tube=False,
    well_coating=None,
    sterile=False,
    well_count=96,
    col_count=12,
    well_depth_mm=Unit(10.5, "millimeter"),
    well_volume_ul=Unit(320, "microliter"),
    dead_volume_ul=Unit(50, "microliter"),
    safe_min_volume_ul=Unit(50, "microliter"),
    capabilities=[
        "pipette",
        "spin",
        "incubate",
        "cover",
        "stamp",
        "dispense-destination",
        "provision",
        "uncover",
        "seal",
        "unseal",
    ],
    cover_types=["universal"],
    seal_types=["ultra-clear", "foil"],
    vendor="Corning",
    cat_no="353077",
)

#:
FLAT96DELTA = ContainerType(
    name="Nunc MicroWell 96-Well, Nunclon Delta-Treated, Flat-Bottom Microplate",
    shortname="96-flat-white-dc",
    is_tube=False,
    well_coating=None,
    sterile=True,
    well_count=96,
    col_count=12,
    well_depth_mm=Unit(11.2, "millimeter"),
    well_volume_ul=Unit(320, "microliter"),
    dead_volume_ul=Unit(50, "microliter"),
    safe_min_volume_ul=Unit(50, "microliter"),
    capabilities=[
        "pipette",
        "spin",
        "incubate",
        "cover",
        "stamp",
        "dispense-destination",
        "provision",
        "uncover",
        "seal",
        "unseal",
        "liquid_handle",
        "absorbance",
        "fluorescence",
        "luminescence",
    ],
    cover_types=["low_evaporation", "standard", "universal"],
    seal_types=["ultra-clear", "foil"],
    vendor="ThermoFisher",
    cat_no="136101",
)

#:
FLAT384BLACKUBOTTOM = ContainerType(
    name="384-well Black Clear Round Bottom Ultra-low Attachment Microplate",
    shortname="384-ubottom-black-clear-tc",
    is_tube=False,
    well_coating=None,
    sterile=True,
    well_count=384,
    col_count=24,
    well_depth_mm=12.55,
    well_volume_ul=Unit(90, "microliter"),
    dead_volume_ul=Unit(10, "microliter"),
    safe_min_volume_ul=Unit(20, "microliter"),
    capabilities=[
        "pipette",
        "spin",
        "incubate",
        "cover",
        "stamp",
        "dispense",
        "dispense-destination",
        "echo_dest",
        "provision",
        "uncover",
        "seal",
        "unseal",
        "liquid_handle",
        "absorbance",
        "fluorescence",
        "luminescence",
        "bluewash",
        "spectophotometry",
    ],
    cover_types=["universal"],
    seal_types=["ultra-clear", "foil"],
    vendor="Corning",
    cat_no="3830",
)

#:
FLAT384BLACKTC = ContainerType(
    name="384-well Black Clear Flat Bottom Tissue Culture Microplate",
    shortname="384-flat-black-clear-tc",
    is_tube=False,
    well_coating=None,
    sterile=True,
    well_count=384,
    col_count=24,
    well_depth_mm=11.55,
    well_volume_ul=Unit(90, "microliter"),
    dead_volume_ul=Unit(20, "microliter"),
    safe_min_volume_ul=Unit(20, "microliter"),
    capabilities=[
        "pipette",
        "spin",
        "incubate",
        "cover",
        "stamp",
        "dispense",
        "dispense-destination",
        "echo_dest",
        "provision",
        "uncover",
        "seal",
        "unseal",
        "liquid_handle",
        "absorbance",
        "fluorescence",
        "luminescence",
        "bluewash",
        "spectophotometry",
    ],
    cover_types=["universal", "standard"],
    seal_types=["ultra-clear", "foil"],
    vendor="Corning",
    cat_no="3764",
)

_CONTAINER_TYPES = {
    "384-flat": FLAT384,
    "384-pcr": PCR384,
    "384-echo": ECHO384,
    "384-flat-white-white-lv": FLAT384WHITELV,
    "384-flat-white-white-tc": FLAT384WHITETC,
    "384-flat-clear-clear": FLAT384CLEAR,
    "96-flat": FLAT96,
    "96-flat-uv": FLAT96UV,
    "96-pcr": PCR96,
    "96-deep": DEEP96,
    "96-v-kf": V96KF,
    "96-deep-kf": DEEP96KF,
    "24-deep": DEEP24,
    "micro-2.0": MICRO2,
    "micro-1.5": MICRO15,
    "6-flat": FLAT6,
    "1-flat": FLAT1,
    "6-flat-tc": FLAT6TC,
    "res-sw96-hp": RESSW96HP,
    "res-mw8-hp": RESMW8HP,
    "res-mw12-hp": RESMW12HP,
    "96-flat-clear-clear-tc": FLAT96CLEARTC,
    "384-v-clear-clear": V384CLEAR,
    "384-round-clear-clear": ROUND384CLEAR,
    "res-sw384-lp": RESSW384LP,
    "384-echo-ldv": ECHO384LDV,
    "384-echo-ldv-plus": ECHO384LDVPLUS,
    "384-flat-white-clear": FLAT384WHITECLEAR,
    "96-well-v-bottom": V96CC,
    "96-ubottom-clear-tc": FALCON96UBOTTOM,
    "96-flat-white-dc": FLAT96DELTA,
    "384-ubottom-black-clear-tc": FLAT384BLACKUBOTTOM,
    "384-flat-black-clear-tc": FLAT384BLACKTC,
}
