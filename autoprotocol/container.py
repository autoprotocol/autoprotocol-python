from .unit import Unit

class Well(object):

    def __init__(self, container, idx):
        self.container = container
        self.idx = idx
        self.volume = None

    def set_volume(self, vol):
        self.volume = Unit.fromstring(vol)
        return self

    def humanize(self):
        return self.container.humanize(self.idx)

    def __repr__(self):
        return "Well(%s, %s, %s)" % (str(self.container), str(self.idx),
                                     str(self.volume))


class WellGroup(object):

    def __init__(self, wells):
        self.wells = wells

    def set_volume(self, vol):
        for w in self.wells:
            w.set_volume(vol)
        return self

    def indices(self):
        indices = []
        for w in self.wells:
            assert w.container == self.wells[
                0].container, "All wells in WellGroup must belong to the same \
                               container to get their indices"
            indices.append(str(w.idx))
        return indices

    def append(self, other):
        return self.wells.append(other)

    def __getitem__(self, key):
        return self.wells[key]

    def __len__(self):
        return len(self.wells)

    def __repr__(self):
        return "WellGroup(%s)" % (str(self.wells))

    def __add__(self, other):
        return WellGroup(self.wells + other.wells)


class Container(object):

    def __init__(self, id, container_type):
        self.id = id
        self.container_type = container_type
        self._wells = [Well(self, idx)
                       for idx in xrange(container_type.well_count)]

    def well(self, i):
        return self._wells[self.robotize(i)]

    def wells(self, *args):
        return WellGroup([self.well(i) for i in args])

    def robotize(self, well_ref):
        return self.container_type.robotize(well_ref)

    def humanize(self, well_ref):
        return self.container_type.humanize(well_ref)

    def decompose(self, well_ref):
        return self.container_type.decompose(well_ref)

    def all_wells(self, columnwise=False):
        if columnwise:
            num_cols = self.container_type.col_count
            num_rows = self.container_type.well_count / num_cols
            return WellGroup([self._wells[row * num_cols + col]
                              for col in xrange(num_cols)
                              for row in xrange(num_rows)])
        else:
            return WellGroup(self._wells)

    def wells_from(self, start, num, columnwise=False):
        start = self.robotize(start)
        if columnwise:
            row, col = self.decompose(start)
            num_rows = self.container_type.well_count / \
                self.container_type.col_count
            start = col * num_rows + row
        return WellGroup(self.all_wells(columnwise).wells[start:start + num])
