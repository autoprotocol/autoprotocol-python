from .unit import Unit

class Well(object):
    """
    A Well object describes a single location within a container.

    Do not construct a Well directly -- retrieve it from the related Container
    object.

    Attributes
    ----------
    container : Container
        The Container this well belongs to
    index : integer
        The index of this well within the container

    """
    def __init__(self, container, index):
        self.container = container
        self.index = index
        self.volume = None

    def set_volume(self, vol):
        """
        Set the theoretical volume of liquid in this well.

        Used by Protocol.fill_wells()."""
        self.volume = Unit.fromstring(vol)
        return self

    def humanize(self):
        """Return humanized ("A1") formatted index of this Well.
        """
        return self.container.humanize(self.index)

    def __repr__(self):
        """

        """
        return "Well(%s, %s, %s)" % (str(self.container), str(self.index),
                                     str(self.volume))


class WellGroup(object):
    """
    A logical grouping of Wells.

    Wells in a WellGroup do not necessarily need to be in the same container.

    Attributes
    ----------
    wells : list
        List of Well objects contained in this WellGroup

    """

    def __init__(self, wells):
        self.wells = wells

    def set_volume(self, vol):
        """
        Set the volume of every well in the group to vol.
        Must be called on a WellGroup when it is the source in a
        Protocol.distribute() call

        Parameters
        ----------
        vol : str
            Theoretical volume of each well in the WellGroup

        """
        for w in self.wells:
            w.set_volume(vol)
        return self

    def indices(self, human=False):
        """
        Return the indices of the wells in the group, given that all of the
        wells belong to the same container.

        Parameters
        ----------
        human : bool, optionally
            Specify whether list of wells should be in robot (0,1,2...) or
            humanized ("A1", "A2", "A3"...) form

        """
        indices = []
        for w in self.wells:
            assert w.container == self.wells[0].container, "All wells in \
                WellGroup must belong to the same container to get their indices"
            if human:
                indices.append(w.humanize())
            else:
                indices.append(w.index)
        return indices

    def append(self, other):
        """
        Append another well to this WellGroup

        Parameters
        ----------
        other : Well
            Well to append to the WellGroup
        """
        if other in self.wells:
            raise RuntimeError("That Well is already a part of this WellGroup")
        else:
            return self.wells.append(other)

    def __getitem__(self, key):
        """

        """
        return self.wells[key]

    def __len__(self):
        """

        """
        return len(self.wells)

    def __repr__(self):
        """

        """
        return "WellGroup(%s)" % (str(self.wells))

    def __add__(self, other):
        """

        """
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

        .. code-block:: python

            container.wells(i1, i2, i3, ...):
              the i1'th, i2'th, i3'th, ... wells

            container.all_wells(columnwise=False):
              all the wells in the container, optionally arranged columnwise

            container.wells_from(start, num, columnwise=False):
              num wells, starting at well start, and proceeding along the row (or
              column, if columnwise is specified)

    Attributes
    ----------
    id : string
    container_type : ContainerType

    """

    def __init__(self, id, container_type):
        self.id = id
        self.container_type = container_type
        self._wells = [Well(self, idx)
                       for idx in xrange(container_type.well_count)]

    def well(self, i):
        """
        Return a Well object representing the well at the index specified of
        this Container.

        Parameters
        ----------
        i : int, str
            Well reference in the form of an integer (ex: 0) or human-readable
            string (ex: "A1")

        """
        return self._wells[self.robotize(i)]

    def wells(self, *args):
        """
        Return a WellGroup containing references to wells corresponding to the
        index or indices given.

        args : str, int, list
            Reference or list of references to a well index either as an integer
            or a string

        """
        return WellGroup([self.well(i) for i in args])

    def robotize(self, well_ref):
        """
        Return the integer representation of the well index given, based on
        the ContainerType of the Container

        Parameters
        ----------
        well_ref : str
            Well index in human-readable form

        Returns
        -------
        well_ref : int
            Well index passed as an integer

        """
        return self.container_type.robotize(well_ref)

    def humanize(self, well_ref):
        """
        Return the human readable representation of the integer well index
        given based on the ContainerType of the Container

        Parameters
        ----------
        well_ref : int
            Well index in integer form

        Returns
        -------
        well_ref : str
            Well index passed as a string

        """
        return self.container_type.humanize(well_ref)

    def decompose(self, well_ref):
        """
        Return a tuple representing the column and row number of the well
        index given based on the ContainerType of the Container

        Parameters
        ----------
        well_ref : str, int
            Well index in either human-readable or integer form

        Returns
        -------
        well_ref : tuple
            tuple containing the column number and row number of the given
            well_ref

        """
        return self.container_type.decompose(well_ref)

    def all_wells(self, columnwise=False):
        """
        Return a WellGroup representing all Wells belonging to this Container

        Parameters
        ----------
        columnwise : bool, optional
            returns the WellGroup columnwise instead of ordered by well index
            (rowwise)

        """
        if columnwise:
            num_cols = self.container_type.col_count
            num_rows = self.container_type.well_count / num_cols
            return WellGroup([self._wells[row * num_cols + col]
                              for col in xrange(num_cols)
                              for row in xrange(num_rows)])
        else:
            return WellGroup(self._wells)

    def inner_wells(self, columnwise=False):
        """
        Return a WellGroup of all wells on a plate excluding wells in the top and
        bottom rows and in the first and last columns

        """
        num_cols = self.container_type.col_count
        num_rows = self.container_type.row_count()
        inner_wells = []

        if columnwise:
            for c in range(1,num_cols-1):
                wells = []
                for r in range(1, num_rows-1):
                    wells.append((r*num_cols)+c)
                inner_wells.extend(wells)
        else:
            col = num_cols
            for i in range(1,num_rows-1):
                inner_wells.extend(range(col+1, (col+num_cols)-1))
                col += num_cols
        return WellGroup(inner_wells)

    def wells_from(self, start, num, columnwise=False):
        """
        Return a WellGroup of Wells belonging to this Container starting from
        the index indicated (in integer or string form) and including the number
        of proceeding wells specified

        Parameters
        ----------
        start : Well, int, str
            Starting well specified as a Well object, a human-readable well
            index or an integer well index
        num : int
            number of wells to include
        columnwise : bool, optional

        """
        start = self.robotize(start)
        if columnwise:
            row, col = self.decompose(start)
            num_rows = self.container_type.row_count()
            start = col * num_rows + row
        return WellGroup(self.all_wells(columnwise).wells[start:start + num])
