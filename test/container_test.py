import sys
import pytest
from autoprotocol.container import Container, Well, WellGroup
from autoprotocol.unit import Unit

if sys.version_info[0] >= 3:
    xrange = range  # pylint: disable=invalid-name


# pylint: disable=attribute-defined-outside-init
class HasDummyContainers(object):
    @pytest.fixture(autouse=True)
    def make_containers(self, dummy_type):
        self.c = Container(None, dummy_type)
        self.c2 = Container(None, dummy_type)


class TestContainerWellRef(HasDummyContainers):
    def test_well_ref(self):
        assert isinstance(self.c.well("B4"), Well)
        assert isinstance(self.c.well(14), Well)
        with pytest.raises(TypeError):
            self.c.well(1.0)

    def test_decompose(self):
        assert ((2, 3) == self.c.decompose("C4"))
        with pytest.raises(TypeError):
            self.c.decompose(["C4"])

    def test_well_identity(self):
        assert (self.c.well("A1") is self.c.well(0))

    def test_humanize(self):
        assert ("A1" == self.c.well(0).humanize())
        assert ("B3" == self.c.well(7).humanize())
        assert (["A1", "B2"] == self.c.humanize([0, 6]))
        # check bounds
        with pytest.raises(ValueError):
            self.c.humanize(20)
        with pytest.raises(ValueError):
            self.c.humanize(-1)
        # check input type
        with pytest.raises(TypeError):
            self.c.humanize(self.c.well(0))

    def test_robotize(self):
        assert (0 == self.c.robotize("A1"))
        assert (7 == self.c.robotize("B3"))
        assert ([0, 6] == self.c.robotize(["A1", "B2"]))
        # check bounds
        with pytest.raises(ValueError):
            self.c.robotize("A10")
        with pytest.raises(ValueError):
            self.c.robotize("J1")
        # check input type
        with pytest.raises(TypeError):
            self.c.robotize(["A1", 0.1])


class TestContainerWellGroupConstruction(HasDummyContainers):
    def test_tube_error(self):
        # tube() should raise AttributeError if container is not tube
        with pytest.raises(AttributeError):
            self.c.tube()

    def test_tube(self, dummy_tube):
        # tube() should return well 0
        w = dummy_tube.tube()
        assert (0 == w.index)

    def test_all_wells(self):
        # all_wells() should return wells in row-dominant order
        ws = self.c.all_wells()
        assert (15 == len(ws))
        for i in xrange(15):
            assert (i == ws[i].index)

    def test_columnwise(self):
        # or column-dominant order if columnwise
        ws = self.c.all_wells(columnwise=True)
        assert (15 == len(ws))
        row_count = (
            self.c.container_type.well_count / self.c.container_type.col_count
        )
        for i in xrange(15):
            row, col = self.c.decompose(ws[i].index)
            assert (i == row + col * row_count)

    def test_innerwells(self, dummy_big):
        # row-dominant order
        ws = dummy_big.inner_wells()
        assert (6 == len(ws))
        assert ([6, 7, 8, 11, 12, 13] == [i.index for i in ws])
        # column dominant order
        ws = dummy_big.inner_wells(columnwise=True)
        assert ([6, 11, 7, 12, 8, 13] == [i.index for i in ws])

    def test_wells(self):
        ws = self.c.wells([0, 1, 2])
        assert (3 == len(ws))
        assert isinstance(ws, WellGroup)
        ws = self.c.wells("A1", ["A2", "A3"])
        assert (3 == len(ws))
        assert isinstance(ws, WellGroup)
        with pytest.raises(ValueError):
            ws = self.c.wells("an invalid reference")
        with pytest.raises(TypeError):
            ws = self.c.wells({"unexpected": "collection"})

    def test_wells_from(self):
        # wells_from should return the correct things
        ws = self.c.wells_from("A1", 6)
        assert ([0, 1, 2, 3, 4, 5] == [w.index for w in ws])

        ws = self.c.wells_from("B3", 6)
        assert ([7, 8, 9, 10, 11, 12] == [w.index for w in ws])

        ws = self.c.wells_from("A1", 6, columnwise=True)
        assert ([0, 5, 10, 1, 6, 11] == [w.index for w in ws])

        ws = self.c.wells_from("B3", 6, columnwise=True)
        assert ([7, 12, 3, 8, 13, 4] == [w.index for w in ws])

        with pytest.raises(TypeError):
            self.c.wells_from(["unexpected collection"], 4)
        with pytest.raises(TypeError):
            self.c.wells_from("B3", 3.14)

    def test_setter_typechecking(self):
        ws = self.c.all_wells()
        with pytest.raises(TypeError):
            ws.set_properties(["not", "a", "dictionary"])
        with pytest.raises(TypeError):
            ws.set_volume(200)

    def test_append(self):
        ws = self.c.all_wells()
        assert (15 == len(ws))
        ws.append(self.c2.well(0))
        assert (16 == len(ws))
        with pytest.raises(TypeError):
            ws.append("not a well")

    def test_extend(self):
        ws = self.c.all_wells()
        assert (15 == len(ws))
        ws.extend(self.c2.all_wells())
        assert (30 == len(ws))
        with pytest.raises(TypeError):
            ws.extend(self.c2.well(0))

    def test_add(self):
        ws = self.c.all_wells()
        assert (15 == len(ws))
        ws_bigger = self.c.all_wells() + self.c2.all_wells()
        assert (30 == len(ws_bigger))
        ws_plus_well = ws + self.c2.well(0)
        assert (16 == len(ws_plus_well))
        with pytest.raises(TypeError):
            ws = ws + "not a well"

    def test_quadrant(
        self, dummy_96, dummy_384, dummy_1536, dummy_pathological
    ):
        for plate in dummy_96, dummy_384:
            ws = plate.quadrant(0)
            assert (96 == len(ws))
            assert isinstance(ws, WellGroup)

        quadB1 = dummy_384.quadrant("B1")
        assert (96 == len(quadB1))
        assert (24 == quadB1[0].index)
        assert (26 == quadB1[1].index)

        # unsupported plate geometries
        for plate in dummy_1536, dummy_pathological:
            with pytest.raises(ValueError):
                plate.quadrant(0)

        # bogus quadrants
        with pytest.raises(ValueError):
            dummy_96.quadrant("B2")

        with pytest.raises(ValueError):
            dummy_384.quadrant(9)


class TestWellVolume(HasDummyContainers):
    def test_set_volume(self):
        self.c.well(0).set_volume("20:microliter")
        assert (Unit(20, "microliter") == self.c.well(0).volume)
        assert ("microliter" == self.c.well(0).volume.unit)
        assert (self.c.well(1).volume is None)

    def test_set_volume_through_group(self):
        self.c.all_wells().set_volume("30:microliter")
        for w in self.c.all_wells():
            assert (Unit(30, "microliter") == w.volume)

    def test_set_volume_unit_conv(self):
        self.c.well(0).set_volume("200:nanoliter")
        assert (self.c.well(0).volume == Unit(0.2, "microliter"))
        self.c.well(1).set_volume(".1:milliliter")
        assert (self.c.well(1).volume == Unit(100, "microliter"))
        with pytest.raises(ValueError):
            self.c.well(2).set_volume("1:milliliter")

    def test_default_true_max_vol(self, dummy_384, dummy_tube):
        assert (dummy_tube.container_type.true_max_vol_ul ==
                dummy_tube.container_type.well_volume_ul)
        assert (dummy_384.container_type.true_max_vol_ul ==
                dummy_384.container_type.well_volume_ul)

    def test_echo_max_vol(self):
        from autoprotocol.protocol import Protocol
        p = Protocol()
        echo_w = p.ref("echo", None, "384-echo", discard=True).well(0)
        echo_w.set_volume("135:microliter")
        assert echo_w.volume == Unit(135, "microliter")
        with pytest.raises(ValueError):
            echo_w.set_volume("136:microliter")


class TestWellProperty(HasDummyContainers):
    def test_set_properties(self):
        self.c.well(0).set_properties(
            {"Concentration": "40:nanogram/microliter"}
        )
        assert isinstance(self.c.well(0).properties, dict)
        assert (["Concentration"] ==
                list(self.c.well(0).properties.keys()))
        assert (["40:nanogram/microliter"] ==
                list(self.c.well(0).properties.values()))
        self.c.well(0).set_properties({"Dilution": "1"})
        assert (["Dilution"] ==
                list(self.c.well(0).properties.keys()))
        assert (["1"] ==
                list(self.c.well(0).properties.values()))
        with pytest.raises(TypeError):
            self.c.well(0).set_properties(["property", "value"])
        with pytest.raises(TypeError):
            self.c.well(0).set_properties({"property", True})
        with pytest.raises(TypeError):
            self.c.well(0).set_properties({("property"), "value"})

    def test_add_properties(self):
        self.c.well(0).add_properties({"nickname": "dummy"})
        assert (len(self.c.well(0).properties.keys()) == 1)
        self.c.well(0).add_properties({"nickname": "dummy2"})
        assert (len(self.c.well(0).properties.keys()) == 1)
        assert (["dummy2"] ==
                list(self.c.well(0).properties.values()))
        self.c.well(0).add_properties(
            {"concentration": "12:nanogram/microliter"}
        )
        assert (len(self.c.well(0).properties.keys()) == 2)
        self.c.well(0).add_properties({"property1": "2", "ratio": "1:10"})
        assert (len(self.c.well(0).properties.keys()) == 4)
        with pytest.raises(TypeError):
            self.c.well(0).add_properties(["property", "value"])

    def test_properties_copy(self):
        self.c.well(0).set_properties(
            {"Concentration": "40:nanogram/microliter"}
        )
        self.c2.well(0).set_properties(self.c.well(0).properties)
        self.c2.well(0).add_properties({"nickname": "dummy"})
        assert (["Concentration"] ==
                list(self.c.well(0).properties.keys()))
        assert (["40:nanogram/microliter"] ==
                list(self.c.well(0).properties.values()))
        self.c2.well(0).set_properties({"nickname": "dummy"})
        assert (["Concentration"] ==
                list(self.c.well(0).properties.keys()))
        assert (["40:nanogram/microliter"] ==
                list(self.c.well(0).properties.values()))

    def test_add_properties_wellgroup(self):
        group = self.c.wells_from(0, 3).set_properties(
            {"property1": "value1", "property2": "value2"}
        )
        self.c.well(0).add_properties({"property4": "value4"})
        assert (len(self.c.well(0).properties.keys()) == 3)
        for well in group:
            assert ("property1" in well.properties)
            assert ("property2" in well.properties)


class TestWellName(HasDummyContainers):
    def test_set_name(self):
        self.c.well(0).set_name("sample")
        assert (self.c.well(0).name == "sample")


class TestWellGroupName(HasDummyContainers):
    def test_set_group_name(self):
        ws = self.c.all_wells()
        ws.set_group_name("test_name")
        assert (ws.name == "test_name")


class TestWellGroupList(HasDummyContainers):
    def test_wells_with(self):
        ws = self.c.wells_from('A1', 2)
        ws.set_properties({'property1': 'value1'})
        prop = ws.wells_with('property1')
        assert ("property1" in prop[0].properties)
        assert ("property1" in prop[1].properties)
        ws2 = self.c.wells_from('B1', 2)
        ws2.set_properties({'property2': 'value2'})
        ws.extend(ws2)
        assert ("property1" not in ws[2].properties)
        assert ("property1" not in ws[3].properties)
        assert ("property2" in ws[2].properties)
        assert ("property2" in ws[3].properties)
        ws[2].set_properties({'property1': 'value2'})
        ws[3].set_properties({'property1': 'value2'})
        prop = ws.wells_with('property1')
        assert (len(prop) == 4)
        prop_and_val = ws.wells_with('property1', 'value2')
        assert (prop_and_val[0] == ws[2])
        assert (prop_and_val[1] == ws[3])

    def test_pop(self):
        ws = self.c.wells_from('A1', 3)
        assert (ws[0] == ws.pop(0))
        assert (ws[-1] == ws.pop())
        assert (len(ws) == 1)
        assert (ws[-1] == ws.pop())
        assert (len(ws) == 0)

    def test_insert(self):
        ws = self.c.wells('A1', 2)
        insert_wells = self.c.wells_from('C1', 3)
        ws.insert(1, insert_wells[0])
        assert (ws[1] == insert_wells[0])
        ws.insert(0, insert_wells[1])
        assert (ws[0] == insert_wells[1])
        ws.insert(100, insert_wells[2])
        assert (ws[-1] == insert_wells[2])
        assert (len(ws) == 5)


class TestWellGroupEquality(HasDummyContainers):
    def test_equality(self):
        assert self.c.wells([0]) == self.c.wells([0])

    def test_inequality(self):
        assert self.c.wells([0]) != self.c.wells([1])


class TestContainerVolumes(object):
    def test_true_vol_default(self, dummy_tube, dummy_96):
        assert (dummy_96.container_type.true_max_vol_ul ==
                dummy_96.container_type.well_volume_ul)
        assert (dummy_tube.container_type.true_max_vol_ul ==
                dummy_tube.container_type.well_volume_ul)


class TestAliquotProperties(HasDummyContainers):
    def test_wells(self):
        self.c.well(0).add_properties({"test0": "true"})
        assert(self.c.well(0).properties["test0"] == "true")

        self.c.well(0).set_properties({"test1": "true"})
        assert(self.c.well(0).properties == {"test1": "true"})

        assert(self.c.well(3).properties == {})

    def test_well_groups(self):
        self.c.wells(0, 1).add_properties({"test0": "true"})
        assert(self.c.well(1).properties["test0"] == "true")

        self.c.wells(0, 1).set_properties({"test1": "true"})
        assert(self.c.well(1).properties == {"test1": "true"})

        assert(self.c.well(3).properties == {})

    def test_correct_formatting(self):
        with pytest.raises(TypeError):
            self.c.well(0).add_properties({True: "True"})
        with pytest.raises(TypeError):
            self.c.well(0).add_properties({"True": True})
        with pytest.raises(TypeError):
            self.c.well(0).add_properties([])
