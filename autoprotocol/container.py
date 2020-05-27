"""
Container, Well, WellGroup objects and associated functions

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

import json
import warnings

from .constants import SBS_FORMAT_SHAPES
from .unit import Unit

SEAL_TYPES = ["ultra-clear", "foil", "breathable"]
COVER_TYPES = ["standard", "low_evaporation", "universal"]


class Well(object):
    """
    A Well object describes a single location within a container.

    Do not construct a Well directly -- retrieve it from the related Container
    object.

    Parameters
    ----------
    container : Container
        The Container this well belongs to.
    index : int
        The index of this well within the container.

    """

    def __init__(self, container, index):
        self.container = container
        self.index = index
        self.volume = None
        self.name = None
        self.properties = {}

    @staticmethod
    def validate_properties(properties):
        if not isinstance(properties, dict):
            raise TypeError(
                f"Aliquot properties {properties} are of type "
                f"{type(properties)}, they should be a `dict`."
            )
        for key, value in properties.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"Aliquot property {key} : {value} has a key of type "
                    f"{type(key)}, it should be a 'str'."
                )
            try:
                json.dumps(value)
            except TypeError:
                raise TypeError(
                    f"Aliquot property {key} : {value} has a value of type "
                    f"{type(value)}, that isn't JSON serializable."
                )

    def set_properties(self, properties):
        """
        Set properties for a Well. Existing property dictionary
        will be completely overwritten with the new dictionary.

        Parameters
        ----------
        properties : dict
            Custom properties for a Well in dictionary form.

        Returns
        -------
        Well
            Well with modified properties
        """
        self.validate_properties(properties)
        self.properties = properties.copy()
        return self

    def add_properties(self, properties):
        """
        Add properties to the properties attribute of a Well.

        If any property with the same key already exists for the Well then:
         - if both old and new properties are lists then append the new property
         - otherwise overwrite the old property with the new one

        Parameters
        ----------
        properties : dict
            Dictionary of properties to add to a Well.

        Returns
        -------
        Well
            Well with modified properties
        """
        self.validate_properties(properties)
        for key, value in properties.items():
            if key in self.properties:
                values_are_lists = all(
                    isinstance(_, list) for _ in [value, self.properties[key]]
                )
                if values_are_lists:
                    self.properties[key].extend(value)
                else:
                    message = f"Overwriting existing property {key} for {self}"
                    warnings.warn(message=message)
                    self.properties[key] = value
            else:
                self.properties[key] = value
        return self

    def set_volume(self, vol):
        """
        Set the theoretical volume of liquid in a Well.

        Parameters
        ----------
        vol : str, Unit
            Theoretical volume to indicate for a Well.

        Returns
        -------
        Well
            Well with modified volume

        Raises
        ------
        TypeError
            Incorrect input-type given
        ValueError
            Volume set exceeds maximum well volume
        """
        if not isinstance(vol, str) and not isinstance(vol, Unit):
            raise TypeError(
                f"Volume {vol} is of type {type(vol)}, it should be either "
                f"'str' or 'Unit'."
            )
        v = Unit(vol)
        max_vol = self.container.container_type.true_max_vol_ul
        if v > max_vol:
            raise ValueError(
                f"Theoretical volume {v} to be set exceeds maximum well "
                f"volume {max_vol}."
            )
        self.volume = v
        return self

    def set_name(self, name):
        """
        Set a name for this well for it to be included in a protocol's
        "outs" section

        Parameters
        ----------
        name : str
            Well name.

        Returns
        -------
        Well
            Well with modified name
        """
        self.name = name
        return self

    def humanize(self):
        """
        Return the human readable representation of the integer well index
        given based on the ContainerType of the Well.

        Uses the humanize function from the ContainerType class. Refer to
        `ContainerType.humanize()` for more information.

        Returns
        -------
        str
            Index of well in Container (in human readable form)
        """
        return self.container.humanize(self.index)

    def available_volume(self):
        """
        Returns the available volume of a Well.
        This is calculated as nominal volume - container_type dead volume

        Returns
        -------
        Unit(volume)
            Volume in well

        Raises
        ------
        RuntimeError
            Well has no volume
        """
        if self.volume is None:
            raise RuntimeError(f"well {self} has no volume")
        return self.volume - self.container.container_type.dead_volume_ul

    def __repr__(self):
        """
        Return a string representation of a Well.

        """
        return f"Well({str(self.container)}, {str(self.index)}, " f"{str(self.volume)})"


class WellGroup(object):
    """
    A logical grouping of Wells.

    Wells in a WellGroup do not necessarily need to be in the same container.

    Parameters
    ----------
    wells : list
        List of Well objects contained in this WellGroup.

    Raises
    ------
    TypeError
        Wells is not of the right input type

    """

    def __init__(self, wells):
        if isinstance(wells, Well):
            wells = [wells]
        elif isinstance(wells, WellGroup):
            wells = wells.wells
        elif isinstance(wells, list):
            if not all(isinstance(well, Well) for well in wells):
                raise TypeError("All elements in list must be wells")
        else:
            raise TypeError("Wells must be Well, list of wells, WellGroup.")

        self.wells = wells
        self.name = None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def set_properties(self, properties):
        """
        Set the same properties for each Well in a WellGroup.

        Parameters
        ----------
        properties : dict
            Dictionary of properties to set on Well(s).

        Returns
        -------
        WellGroup
            WellGroup with modified properties

        """
        for w in self.wells:
            w.set_properties(properties)
        return self

    def add_properties(self, properties):
        """
        Add the same properties for each Well in a WellGroup.

        Parameters
        ----------
        properties : dict
            Dictionary of properties to set on Well(s).

        Returns
        -------
        WellGroup
            WellGroup with modified properties

        """
        for w in self.wells:
            w.add_properties(properties)
        return self

    def set_volume(self, vol):
        """
        Set the volume of every well in the group to vol.

        Parameters
        ----------
        vol : Unit, str
            Theoretical volume of each well in the WellGroup.

        Returns
        -------
        WellGroup
            WellGroup with modified volume

        """
        for w in self.wells:
            w.set_volume(vol)
        return self

    def indices(self):
        """
        Return the indices of the wells in the group in human-readable form,
        given that all of the wells belong to the same container.

        Returns
        -------
        list(str)
            List of humanized indices from this WellGroup
        """
        indices = []
        for w in self.wells:
            assert w.container == self.wells[0].container, (
                "All wells in WellGroup must belong to the same container to "
                "get their indices."
            )
            indices.append(w.humanize())

        return indices

    def append(self, other):
        """
        Append another well to this WellGroup.

        Parameters
        ----------
        other : Well
            Well to append to this WellGroup.

        Returns
        -------
        WellGroup
            WellGroup with appended well

        Raises
        ------
        TypeError
            other is not of type Well

        """
        if not isinstance(other, Well):
            raise TypeError("Input given is not of type 'Well'.")
        else:
            return self.wells.append(other)

    def extend(self, other):
        """
        Extend this WellGroup with another WellGroup.

        Parameters
        ----------
        other : WellGroup or list of Wells
            WellGroup to extend this WellGroup.

        Returns
        -------
        WellGroup
            WellGroup extended with specified WellGroup

        Raises
        ------
        TypeError
            Input WellGroup is not of the right type

        """
        if not isinstance(other, (WellGroup, list)):
            raise TypeError("Input given is not of type 'WellGroup' or " "'list'.")
        else:
            if not all(isinstance(well, Well) for well in other):
                raise TypeError("Input given is not of type 'Well'.")
            return self.wells.extend(WellGroup(other).wells)

    def set_group_name(self, name):
        """
        Assigns a name to a WellGroup.

        Parameters
        ----------
        name: str
            WellGroup name

        Returns
        -------
        str
            Name of wellgroup
        """
        self.name = name
        return self

    def wells_with(self, prop, val=None):
        """
        Returns a wellgroup of wells with the specified property and value

        Parameters
        ----------
        prop: str
            the property you are searching for
        val: str, optional
            the value assigned to the property

        Returns
        -------
        WellGroup
            WellGroup with modified properties

        Raises
        ------
        TypeError
            property or value defined does not have right input type

        """
        if not isinstance(prop, str):
            raise TypeError(f"property is not a string: {prop!r}")
        if val is not None:
            return WellGroup(
                [
                    w
                    for w in self.wells
                    if prop in w.properties and w.properties[prop] is val
                ]
            )
        else:
            return WellGroup([w for w in self.wells if prop in w.properties])

    def pop(self, index=-1):
        """
        Removes and returns the last well in the wellgroup, unless an index is
        specified.
        If index is specified, the well at that index is removed from the
        wellgroup and returned.

        Parameters
        ----------
        index: int, optional
            the index of the well you want to remove and return

        Returns
        -------
        Well
            Well with selected index from WellGroup

        """
        return self.wells.pop(index)

    def insert(self, i, well):
        """
        Insert a well at a given position.

        Parameters
        ----------
        i : int
            index to insert the well at
        well : Well
            insert this well at the index

        Returns
        -------
        WellGroup
            WellGroup with inserted wells

        Raises
        ------
        TypeError
            index or well defined does not have right input type

        """
        if not isinstance(i, int):
            raise TypeError("Input given is not of type 'Int'")
        if not isinstance(well, Well):
            raise TypeError("Input given is not of type 'Well'")

        if i >= len(self.wells):
            return self.wells.append(well)
        else:
            self.wells = self.wells[:i] + [well] + self.wells[i:]
            return self.wells

    def __setitem__(self, key, item):
        """
        Set a specific Well in a WellGroup.

        Parameters
        ----------
        key : int
            Position in a WellGroup in robotized form.
        item: Well
            Well or WellGroup to be added

        Raises
        ------
        TypeError
            Item specified is not of type `Well`
        """
        if not isinstance(item, Well):
            raise TypeError("Input given is not of type 'Well'.")
        self.wells[key] = item

    def __getitem__(self, key):
        """
        Return a specific Well from a WellGroup.

        Parameters
        ----------
        key : int
            Position in a WellGroup in robotized form.

        Returns
        -------
        Well
            Specified well from given key
        """
        return self.wells[key]

    def __len__(self):
        """
        Return the number of Wells in a WellGroup.

        """
        return len(self.wells)

    def __repr__(self):
        """
        Return a string representation of a WellGroup.

        """
        return "WellGroup(%s)" % (str(self.wells))

    def __add__(self, other):
        """
        Append a Well or Wells from another WellGroup to this WellGroup.

        Parameters
        ----------
        other : Well, WellGroup.

        Returns
        -------
        WellGroup
            WellGroup with appended wells

        Raises
        ------
        TypeError
            Input given is not of type Well or WellGroup

        """
        if not isinstance(other, (Well, WellGroup)):
            raise TypeError("You can only add a Well or WellGroups " "together.")
        if isinstance(other, Well):
            return WellGroup(self.wells + [other])
        else:
            return WellGroup(self.wells + other.wells)


# pylint: disable=redefined-builtin
class Container(object):
    """
    A reference to a specific physical container (e.g. a tube or 96-well
    microplate).

    Every Container has an associated ContainerType, which defines the well
    count and arrangement, amongst other properties.

    There are several methods on Container which present a convenient interface
    for defining subsets of wells on which to operate. These methods return a
    WellGroup.

    Containers are usually declared using the Protocol.ref method.

    Parameters
    ----------
    id : str, optional
        Alphanumerical identifier for a Container.
    container_type : ContainerType
        ContainerType associated with a Container.
    name : str, optional
        name of the container/ref being created.
    storage : str, optional
        name of the storage condition.
    cover : str, optional
        name of the cover on the container.

    Raises
    ------
    AttributeError
        Invalid cover-type given

    """

    def __init__(self, id, container_type, name=None, storage=None, cover=None):
        self.name = name
        self.id = id
        self.container_type = container_type
        self.storage = storage
        self.cover = cover
        self._wells = [Well(self, idx) for idx in range(container_type.well_count)]
        if self.cover and not (self.is_covered() or self.is_sealed()):
            raise AttributeError(f"{cover} is not a valid seal or cover type.")

    def well(self, i):
        """
        Return a Well object representing the well at the index specified of
        this Container.

        Parameters
        ----------
        i : int, str
            Well reference in the form of an integer (ex: 0) or human-readable
            string (ex: "A1").

        Returns
        -------
        Well
            Well for given reference

        Raises
        ------
        TypeError
            index given is not of the right type
        """
        if not isinstance(i, (int, str)):
            raise TypeError("Well reference given is not of type 'int' or " "'str'.")
        return self._wells[self.robotize(i)]

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
        Well
            The well at position (row, column)
        """
        return self.well(
            self.container_type.well_from_coordinates(row=row, column=column)
        )

    def tube(self):
        """
        Checks if container is tube and returns a Well representing the zeroth
        well.

        Returns
        -------
        Well
            Zeroth well of tube

        Raises
        -------
        AttributeError
            If container is not tube

        """
        if self.container_type.is_tube:
            return self.well(0)
        else:
            raise AttributeError(
                f"{self} is a {self.container_type.shortname} " f"and is not a tube"
            )

    def wells(self, *args):
        """
        Return a WellGroup containing references to wells corresponding to the
        index or indices given.

        Parameters
        ----------
        args : str, int, list
            Reference or list of references to a well index either as an
            integer or a string.

        Returns
        -------
        WellGroup
            Wells from specified references

        Raises
        ------
        TypeError
            Well reference is not of a valid input type
        """
        if isinstance(args[0], list):
            wells = args[0]
        else:
            wells = [args[0]]
        for a in args[1:]:
            if isinstance(a, list):
                wells.extend(a)
            else:
                wells.extend([a])
        for w in wells:
            if not isinstance(w, (str, int, list)):
                raise TypeError(
                    "Well reference given is not of type" " 'int', 'str' or 'list'."
                )

        return WellGroup([self.well(w) for w in wells])

    def robotize(self, well_ref):
        """
        Return the integer representation of the well index given, based on
        the ContainerType of the Container.

        Uses the robotize function from the ContainerType class. Refer to
        `ContainerType.robotize()` for more information.

        """
        if not isinstance(well_ref, (str, int, Well, list)):
            raise TypeError(
                "Well reference given is not of type 'str' " "'int', 'Well' or 'list'."
            )
        return self.container_type.robotize(well_ref)

    def humanize(self, well_ref):
        """
        Return the human readable representation of the integer well index
        given based on the ContainerType of the Container.

        Uses the humanize function from the ContainerType class. Refer to
        `ContainerType.humanize()` for more information.

        """
        if not isinstance(well_ref, (int, str, list)):
            raise TypeError(
                "Well reference given is not of type 'int'," "'str' or 'list'."
            )
        return self.container_type.humanize(well_ref)

    def decompose(self, well_ref):
        """
        Return a tuple representing the column and row number of the well
        index given based on the ContainerType of the Container.

        Uses the decompose function from the ContainerType class. Refer to
        `ContainerType.decompose()` for more information.

        """
        if not isinstance(well_ref, (int, str, Well)):
            raise TypeError(
                "Well reference given is not of type 'int', " "'str' or Well."
            )
        return self.container_type.decompose(well_ref)

    def all_wells(self, columnwise=False):
        """
        Return a WellGroup representing all Wells belonging to this Container.

        Parameters
        ----------
        columnwise : bool, optional
            returns the WellGroup columnwise instead of rowwise (ordered by
            well index).

        Returns
        -------
        WellGroup
            WellGroup of all Wells in Container

        """
        if columnwise:
            num_cols = self.container_type.col_count
            num_rows = self.container_type.well_count // num_cols
            return WellGroup(
                [
                    self._wells[row * num_cols + col]
                    for col in range(num_cols)
                    for row in range(num_rows)
                ]
            )
        else:
            return WellGroup(self._wells)

    def inner_wells(self, columnwise=False):
        """
        Return a WellGroup of all wells on a plate excluding wells in the top
        and bottom rows and in the first and last columns.

        Parameters
        ----------
        columnwise : bool, optional
            returns the WellGroup columnwise instead of rowwise (ordered by
            well index).

        Returns
        -------
        WellGroup
            WellGroup of inner wells

        """
        num_cols = self.container_type.col_count
        num_rows = self.container_type.row_count()
        inner_wells = []
        if columnwise:
            for c in range(1, num_cols - 1):
                wells = []
                for r in range(1, num_rows - 1):
                    wells.append((r * num_cols) + c)
                inner_wells.extend(wells)
        else:
            well = num_cols
            for _ in range(1, num_rows - 1):
                inner_wells.extend(range(well + 1, well + (num_cols - 1)))
                well += num_cols
        inner_wells = [self._wells[x] for x in inner_wells]
        return WellGroup(inner_wells)

    def wells_from(self, start, num, columnwise=False):
        """
        Return a WellGroup of Wells belonging to this Container starting from
        the index indicated (in integer or string form) and including the
        number of proceeding wells specified. Wells are counted from the
        starting well rowwise unless columnwise is True.

        Parameters
        ----------
        start : Well or int or str
            Starting well specified as a Well object, a human-readable well
            index or an integer well index.
        num : int
            Number of wells to include in the Wellgroup.
        columnwise : bool, optional
            Specifies whether the wells included should be counted columnwise
            instead of the default rowwise.

        Returns
        -------
        WellGroup
            WellGroup of selected wells

        Raises
        ------
        TypeError
            Incorrect input types, e.g. `num` has to be of type int
        """
        if not isinstance(start, (str, int, Well)):
            raise TypeError(
                "Well reference given is not of type 'str'," "'int', or 'Well'."
            )
        if not isinstance(num, int):
            raise TypeError("Number of wells given is not of type 'int'.")

        start = self.robotize(start)
        if columnwise:
            row, col = self.decompose(start)
            num_rows = self.container_type.row_count()
            start = col * num_rows + row
        return WellGroup(self.all_wells(columnwise).wells[start : start + num])

    def is_sealed(self):
        """
        Check if Container is sealed.
        """
        return self.cover in SEAL_TYPES

    def is_covered(self):
        """
        Check if Container is covered.
        """
        return self.cover in COVER_TYPES

    def quadrant(self, quad):
        """
        Return a WellGroup of Wells corresponding to the selected quadrant of
        this Container.

        Parameters
        ----------
        quad : int or str
            Specifies the quadrant number of the well (ex. 2)

        Returns
        -------
        WellGroup
            WellGroup of wells for the specified quadrant

        Raises
        ------
        ValueError
            Invalid quadrant specified for this Container type

        """
        # TODO(Define what each quadrant number corresponds toL)
        if isinstance(quad, str):
            quad = quad.lower()
            if quad == "a1":
                quad = 0
            elif quad == "a2":
                quad = 1
            elif quad == "b1":
                quad = 2
            elif quad == "b2":
                quad = 3
            else:
                raise ValueError("Invalid quadrant index.")

        # n_wells: n_cols
        allowed_layouts = {96: 12, 384: 24}
        n_wells = self.container_type.well_count
        if (
            n_wells not in allowed_layouts
            or self.container_type.col_count != allowed_layouts[n_wells]
        ):
            raise ValueError(
                "Quadrant is only defined for standard 96 and " "384-well plates"
            )

        if n_wells == 96:
            if quad == 0:
                return WellGroup(self._wells)
            else:
                raise ValueError(
                    "0 or 'A1' is the only valid quadrant for a 96-well " "plate."
                )

        if quad not in [0, 1, 2, 3]:
            raise ValueError(
                f"Invalid quadrant {quad} for plate type " f"{str(self.name)}"
            )

        start_well = [0, 1, 24, 25]
        wells = []

        for row_offset in range(start_well[quad], 384, 48):
            for col_offset in range(0, 24, 2):
                wells.append(row_offset + col_offset)

        return self.wells(wells)

    def set_storage(self, storage):
        """
        Set the storage condition of a container, will overwrite
        an existing storage condition, will remove discard True.

        Parameters
        ----------
        storage : str
            Storage condition.

        Returns
        -------
        Container
            Container with modified storage condition

        Raises
        ----------
        TypeError
            If storage condition not of type str.

        """
        if not isinstance(storage, str):
            raise TypeError(
                f"Storage condition given ({storage}) is not of "
                f"type str. {type(storage)}."
            )

        self.storage = storage
        return self

    def discard(self):
        """
        Set the storage condition of a container to None and
        container to be discarded if ref in protocol.

        Example
        ----------

            .. code-block:: python

                p = Protocol()
                container = p.ref("new_container", cont_type="96-pcr",
                                  storage="cold_20")
                p.incubate(c, "warm_37", "30:minute")
                container.discard()

                Autoprotocol generated:

                .. code-block:: json

                   "refs": {
                      "new_container": {
                        "new": "96-pcr",
                        "discard": true
                      }
                    }

        """
        self.storage = None
        return self

    # pylint: disable=too-many-locals
    def wells_from_shape(self, origin, shape):
        """
        Gets a WellGroup that originates from the `origin` and is distributed
        across the container in `shape`. This group has a Well for each index
        in `range(shape["rows"] * shape["columns"])`.

        In cases where the container dimensions are smaller than the shape
        format's dimensions the returned WellGroup will reference some wells
        multiple times. This is analogous to an SBS96-formatted liquid handler
        acting with multiple tips in each well of an SBS24-formatted plate.

        Parameters
        ----------
        origin : int or str
            The index of the top left corner origin of the shape
        shape : dict
            See Also Instruction.builders.shape

        Returns
        -------
        WellGroup
            The group of wells distributed in `shape` from the `origin`

        Raises
        ------
        ValueError
            if the shape exceeds the extents of the container
        """
        from .instruction import Instruction

        shape = Instruction.builders.shape(**shape)
        origin = self.well(origin)

        # unpacking container and shape format properties
        container_rows = self.container_type.row_count()
        container_cols = self.container_type.col_count
        format_rows = SBS_FORMAT_SHAPES[shape["format"]]["rows"]
        format_cols = SBS_FORMAT_SHAPES[shape["format"]]["columns"]

        # getting the row and column values for the origin
        origin_row, origin_col = self.decompose(origin)

        # ratios of container shape to format shape
        row_scaling = container_rows / format_rows
        col_scaling = container_cols / format_cols

        # the 0-indexed coordinates of all wells in origin plate to be included
        well_rows = []
        well_cols = []
        for idx in range(shape["rows"]):
            well_row = int(origin_row + idx * row_scaling)
            well_rows.append(well_row)
        for idx in range(shape["columns"]):
            well_col = int(origin_col + idx * col_scaling)
            well_cols.append(well_col)

        # coordinates of the tail (bottom right well) should not exceed bounds
        tail_row = well_rows[-1]
        tail_col = well_cols[-1]
        # tail_row and tail_col are 0-indexed based
        # container_rows and container_cols are 1-indexed based
        if tail_row + 1 > container_rows or tail_col + 1 > container_cols:
            raise ValueError(
                f"origin: {origin} with shape: {shape} exceeds the bounds of "
                f"container: {self}"
            )

        return WellGroup(
            [self.well_from_coordinates(x, y) for x in well_rows for y in well_cols]
        )

    def __repr__(self):
        """
        Return a string representation of a Container using the specified name.
        (ex. Container('my_plate'))

        """
        return (
            f"Container({str(self.name)}"
            f"{', cover=' + self.cover if self.cover else ''})"
        )
