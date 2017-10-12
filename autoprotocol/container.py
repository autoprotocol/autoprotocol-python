from __future__ import print_function
from .unit import Unit
from .util import quad_ind_to_num
import sys

if sys.version_info[0] >= 3:
    xrange = range
    basestring = str

"""
    :copyright: 2017 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

SEAL_TYPES = ["ultra-clear", "foil"]
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
    index : integer
        The index of this well within the container.
    volume : Unit
        Theoretical volume of this well.
    properties : dict
        Additional properties of this well represented as a dictionary.

    """

    def __init__(self, container, index):
        self.container = container
        self.index = index
        self.volume = None
        self.name = None
        self.properties = {}

    def set_properties(self, properties):
        """
        Set properties for a Well. Existing property dictionary
        will be completely overwritten with the new dictionary.

        Parameters
        ----------
        properties : dict
            Custom properties for a Well in dictionary form.

        """
        if not isinstance(properties, dict):
            raise TypeError("Properties is not of type 'dict'.")
        self.properties = {key: value for key, value in properties.items()}
        return self

    def add_properties(self, properties):
        """
        Add properties to the properties attribute of a Well.
        If any key/value pairs are present in both the old and
        new dictionaries, they will be overwritten by the pairs
        in the new dictionary.

        Parameters
        ----------
        properties : dict
            Dictionary of properties to add to a Well.

        """
        if not isinstance(properties, dict):
            raise TypeError("Properties given is not of type 'dict'.")
        for key, value in properties.items():
            self.properties[key] = value
        return self

    def set_volume(self, vol):
        """
        Set the theoretical volume of liquid in a Well.

        Parameters
        ----------
        vol : str, Unit
            Theoretical volume to indicate for a Well.

        """
        if not isinstance(vol, basestring) and not isinstance(vol, Unit):
            raise TypeError("Volume given is not of type str or "
                            "Unit. %s" % type(vol))
        v = Unit.fromstring(vol)
        if v > self.container.container_type.true_max_vol_ul:
            raise ValueError("Theoretical volume you are trying to set "
                             "exceeds the maximum volume of this well.")
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

        """
        self.name = name
        return self

    def humanize(self):
        """
        Return the human readable representation of the integer well index
        given based on the ContainerType of the Well.

        Uses the humanize function from the ContainerType class. Refer to
        `ContainerType.humanize()` for more information.

        """
        return self.container.humanize(self.index)

    def available_volume(self):
        """
        Returns the available volume of a Well.
        This is calculated as nominal volume - container_type dead volume

        """
        if self.volume is None:
            raise RuntimeError("Well {} has no volume".format(self))
        return self.volume - self.container.container_type.dead_volume_ul

    def __repr__(self):
        """
        Return a string representation of a Well.

        """
        return "Well(%s, %s, %s)" % (str(self.container), str(self.index),
                                     str(self.volume))


class WellGroup(object):
    """
    A logical grouping of Wells.

    Wells in a WellGroup do not necessarily need to be in the same container.

    Parameters
    ----------
    wells : list
        List of Well objects contained in this WellGroup.

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

    def set_properties(self, properties):
        """
        Set the same properties for each Well in a WellGroup.

        Parameters
        ----------
        properties : dict
            Dictionary of properties to set on Well(s).

        """
        if not isinstance(properties, dict):
            raise TypeError("Properties given is not of type 'dict'.")
        for w in self.wells:
            w.set_properties(properties)
        return self

    def set_volume(self, vol):
        """
        Set the volume of every well in the group to vol.

        Parameters
        ----------
        vol : Unit, str
            Theoretical volume of each well in the WellGroup.

        """
        if not isinstance(vol, (Unit, basestring)):
            raise TypeError("Volume given is not of type Unit or 'str'.")
        for w in self.wells:
            w.set_volume(vol)
        return self

    def indices(self):
        """
        Return the indices of the wells in the group in human-readable form,
        given that all of the wells belong to the same container.

        """
        indices = []
        for w in self.wells:
            assert w.container == self.wells[0].container, (
                "All wells in WellGroup must belong to the same container to "
                "get their indices.")
            indices.append(w.humanize())

        return indices

    def append(self, other):
        """
        Append another well to this WellGroup.

        Parameters
        ----------
        other : Well
            Well to append to this WellGroup.

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

        """
        if not isinstance(other, (WellGroup, list)):
            raise TypeError("Input given is not of type 'WellGroup' or "
                            "'list'.")
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
        val: str
            the value assigned to the property
        """
        assert type(prop) is str, "property is not a string: %r" % prop
        assert type(val) is None or str, "value is not a string: %r" % val
        if val:
            return WellGroup([w for w in self.wells if prop in w.properties and
                             w.properties[prop] is val])
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
        index: int
            the index of the well you want to remove and return
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
        """
        assert type(i) is int, "Input given is not of type 'Int'"
        assert type(well) is Well, "Input given is not of type 'Well'"
        if i >= len(self.wells):
            return self.wells.append(well)
        else:
            self.wells = self.wells[:i] + [well] + self.wells[i:]

    def __setitem__(self, key, item):
        """
        Set a specific Well in a WellGroup.

        Parameters
        ----------
        key : int
            Position in a WellGroup in robotized form.
        item: Well
            Well or WellGroup to be added
        """
        assert type(item) is Well, "Input given is not of type 'Well'."
        self.wells[key] = item

    def __getitem__(self, key):
        """
        Return a specific Well from a WellGroup.

        Parameters
        ----------
        key : int
            Position in a WellGroup in robotized form.

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

        """
        if not isinstance(other, (Well, WellGroup)):
            raise TypeError("You can only add a Well or WellGroups "
                            "together.")
        if isinstance(other, Well):
            return WellGroup(self.wells + [other])
        else:
            return WellGroup(self.wells + other.wells)


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
    name : str
        name of the container/ref being created.
    id : string
        Alphanumerical identifier for a Container.
    container_type : ContainerType
        ContainerType associated with a Container.

    """

    def __init__(self, id, container_type, name=None, storage=None,
                 cover=None):
        self.name = name
        self.id = id
        self.container_type = container_type
        self.storage = storage
        self.cover = cover
        self._wells = [Well(self, idx)
                       for idx in xrange(container_type.well_count)]
        if self.cover and not (self.is_covered() or self.is_sealed()):
            raise AttributeError("%s is not a valid seal or cover "
                                 "type." % cover)

    def well(self, i):
        """
        Return a Well object representing the well at the index specified of
        this Container.

        Parameters
        ----------
        i : int, str
            Well reference in the form of an integer (ex: 0) or human-readable
            string (ex: "A1").

        """
        if not isinstance(i, (int, basestring)):
            raise TypeError("Well reference given is not of type 'int' or "
                            "'str'.")
        return self._wells[self.robotize(i)]

    def tube(self):
        """
        Checks if container is tube and returns a Well respresenting the zeroth
        well.

        Returns
        -------
        Well

        Raises
        -------
        AttributeError :
            If container is not tube

        """
        if self.container_type.is_tube:
            return self.well(0)
        else:
            raise AttributeError("%s is a %s and is not a tube" %
                                 (self, self.container_type.shortname))

    def wells(self, *args):
        """
        Return a WellGroup containing references to wells corresponding to the
        index or indices given.

        Parameters
        ----------
        args : str, int, list
            Reference or list of references to a well index either as an
            integer or a string.

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
            if not isinstance(w, (basestring, int, list)):
                raise TypeError("Well reference given is not of type"
                                " 'int', 'str' or 'list'.")

        return WellGroup([self.well(w) for w in wells])

    def robotize(self, well_ref):
        """
        Return the integer representation of the well index given, based on
        the ContainerType of the Container.

        Uses the robotize function from the ContainerType class. Refer to
        `ContainerType.robotize()` for more information.

        """
        if not isinstance(well_ref, (basestring, int, Well, list)):
            raise TypeError("Well reference given is not of type 'str' "
                            "'int', 'Well' or 'list'.")
        return self.container_type.robotize(well_ref)

    def humanize(self, well_ref):
        """
        Return the human readable representation of the integer well index
        given based on the ContainerType of the Container.

        Uses the humanize function from the ContainerType class. Refer to
        `ContainerType.humanize()` for more information.

        """
        if not isinstance(well_ref, (int, basestring, list)):
            raise TypeError("Well reference given is not of type 'int',"
                            "'str' or 'list'.")
        return self.container_type.humanize(well_ref)

    def decompose(self, well_ref):
        """
        Return a tuple representing the column and row number of the well
        index given based on the ContainerType of the Container.

        Uses the decompose function from the ContainerType class. Refer to
        `ContainerType.decompose()` for more information.

        """
        if not isinstance(well_ref, (int, basestring, Well)):
            raise TypeError("Well reference given is not of type 'int', "
                            "'str' or Well.")
        return self.container_type.decompose(well_ref)

    def all_wells(self, columnwise=False):
        """
        Return a WellGroup representing all Wells belonging to this Container.

        Parameters
        ----------
        columnwise : bool, optional
            returns the WellGroup columnwise instead of rowwise (ordered by
            well index).

        """
        if columnwise:
            num_cols = self.container_type.col_count
            num_rows = self.container_type.well_count // num_cols
            return WellGroup([self._wells[row * num_cols + col]
                              for col in xrange(num_cols)
                              for row in xrange(num_rows)])
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

        """
        num_cols = self.container_type.col_count
        num_rows = self.container_type.row_count()
        inner_wells = []
        if columnwise:
            for c in xrange(1, num_cols - 1):
                wells = []
                for r in xrange(1, num_rows - 1):
                    wells.append((r * num_cols) + c)
                inner_wells.extend(wells)
        else:
            well = num_cols
            for i in xrange(1, num_rows - 1):
                inner_wells.extend(xrange(well + 1, well + (num_cols - 1)))
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
        start : Well, int, str
            Starting well specified as a Well object, a human-readable well
            index or an integer well index.
        num : int
            Number of wells to include in the Wellgroup.
        columnwise : bool, optional
            Specifies whether the wells included should be counted columnwise
            instead of the default rowwise.

        """
        if not isinstance(start, (basestring, int, Well)):
            raise TypeError("Well reference given is not of type 'str',"
                            "'int', or 'Well'.")
        if not isinstance(num, (int)):
            raise TypeError("Number of wells given is not of type 'int'.")

        start = self.robotize(start)
        if columnwise:
            row, col = self.decompose(start)
            num_rows = self.container_type.row_count()
            start = col * num_rows + row
        return WellGroup(self.all_wells(columnwise).wells[start:start + num])

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

        This is only applicable to 384-well plates.

        Parameters
        ----------
        quad : int
            Specifies the quadrant number of the well (ex. 2)

        """
        # TODO(Define what each quadrant number corresponds toL)
        if isinstance(quad, str):
            quad = quad_ind_to_num(quad)

        # n_wells: n_cols
        allowed_layouts = {96: 12, 384: 24}
        n_wells = self.container_type.well_count
        if (n_wells not in allowed_layouts or
                self.container_type.col_count != allowed_layouts[n_wells]):
            raise ValueError("Quadrant is only defined for standard 96 and "
                             "384-well plates")

        if n_wells == 96:
            if quad == 0:
                return WellGroup(self._wells)
            else:
                raise ValueError(
                    "0 or 'A1' is the only valid quadrant for a 96-well "
                    "plate.")

        if quad not in [0, 1, 2, 3]:
            raise ValueError("Invalid quadrant {} for plate type {}".format(
                quad, str(self.name)))

        start_well = [0, 1, 24, 25]
        wells = []

        for row_offset in xrange(start_well[quad], 384, 48):
            for col_offset in xrange(0, 24, 2):
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

        Raises
        ----------
        TypeError :
            If storage condition not of type str.

        """
        if not isinstance(storage, basestring):
            raise TypeError("Storage condition given ({0}) is not of type "
                            "str. {1}.".format(storage, type(storage)))

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

    def __repr__(self):
        """
        Return a string representation of a Container using the specified name.
        (ex. Container('my_plate'))

        """
        return "Container(%s%s)" % (str(self.name), ", cover=" +
                                    self.cover if self.cover else "")
