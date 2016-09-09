import sys
import unittest
from autoprotocol.container_type import ContainerType
from autoprotocol.container import Container, Well, WellGroup
from autoprotocol.unit import Unit

if sys.version_info[0] >= 3:
    xrange = range


def make_dummy_type(**kwargs):
    params = {
        "name": "dummy",
        "well_count": 15,
        "well_depth_mm": None,
        "well_volume_ul": Unit(200, "microliter"),
        "well_coating": None,
        "sterile": False,
        "is_tube": False,
        "cover_types": [],
        "seal_types": None,
        "capabilities": [],
        "shortname": "dummy",
        "col_count": 5,
        "dead_volume_ul": Unit(15, "microliter"),
        "safe_min_volume_ul": Unit(30, "microliter")
    }
    params.update(kwargs)
    return ContainerType(**params)

dummy_type = make_dummy_type()


class ContainerWellRefTestCase(unittest.TestCase):

    def setUp(self):
        self.c = Container(None, dummy_type)

    def test_well_ref(self):
        self.assertIsInstance(self.c.well("B4"), Well)
        self.assertIsInstance(self.c.well(14), Well)
        with self.assertRaises(TypeError):
            self.c.well(1.0)

    def test_decompose(self):
        self.assertEqual((2, 3), self.c.decompose("C4"))
        with self.assertRaises(TypeError):
            self.c.decompose(["C4"])

    def test_well_identity(self):
        self.assertIs(self.c.well("A1"), self.c.well(0))

    def test_humanize(self):
        self.assertEqual("A1", self.c.well(0).humanize())
        self.assertEqual("B3", self.c.well(7).humanize())
        self.assertEqual(["A1", "B2"], self.c.humanize([0, 6]))
        # check bounds
        with self.assertRaises(ValueError):
            self.c.humanize(20)
            self.c.humanize(-1)
        # check input type
        with self.assertRaises(TypeError):
            self.c.humanize("10")
            self.c.humanize(self.c.well(0))

    def test_robotize(self):
        self.assertEqual(0, self.c.robotize("A1"))
        self.assertEqual(7, self.c.robotize("B3"))
        self.assertEqual([0, 6], self.c.robotize(["A1", "B2"]))
        # check bounds
        with self.assertRaises(ValueError):
            self.c.robotize("A10")
            self.c.robotize("J1")
        # check input type
        with self.assertRaises(TypeError):
            self.c.robotize(["A1", 0.1])


class ContainerWellGroupConstructionTestCase(unittest.TestCase):

    def setUp(self):
        self.c = Container(None, dummy_type)

    def test_tube_error(self):
        # tube() should raise AttributeError if container is not tube
        with self.assertRaises(AttributeError):
            self.c.tube()

    def test_tube(self):
        # tube() should return well 0
        c = Container(None, make_dummy_type(is_tube=True))
        w = c.tube()
        self.assertEqual(0, w.index)

    def test_all_wells(self):
        # all_wells() should return wells in row-dominant order
        ws = self.c.all_wells()
        self.assertEqual(15, len(ws))
        for i in xrange(15):
            self.assertEqual(i, ws[i].index)

    def test_columnwise(self):
        # or column-dominant order if columnwise
        ws = self.c.all_wells(columnwise=True)
        self.assertEqual(15, len(ws))
        row_count = dummy_type.well_count / dummy_type.col_count
        for i in xrange(15):
            row, col = self.c.decompose(ws[i].index)
            self.assertEqual(i, row + col * row_count)

    def test_innerwells(self):
        big_dummy_type = make_dummy_type(well_count=20)
        c = Container(None, big_dummy_type)
        # row-dominant order
        ws = c.inner_wells()
        self.assertEqual(6, len(ws))
        self.assertEqual([6, 7, 8, 11, 12, 13], [i.index for i in ws])
        # column dominant order
        ws = c.inner_wells(columnwise=True)
        self.assertEqual([6, 11, 7, 12, 8, 13], [i.index for i in ws])

    def test_wells(self):
        ws = self.c.wells([0, 1, 2])
        self.assertEqual(3, len(ws))
        self.assertIsInstance(ws, WellGroup)
        ws = self.c.wells("A1", ["A2", "A3"])
        self.assertEqual(3, len(ws))
        self.assertIsInstance(ws, WellGroup)
        with self.assertRaises(ValueError):
            ws = self.c.wells("an invalid reference")
        with self.assertRaises(TypeError):
            ws = self.c.wells({"unexpected": "collection"})

    def test_wells_from(self):
        # wells_from should return the correct things
        ws = self.c.wells_from("A1", 6)
        self.assertEqual([0, 1, 2, 3, 4, 5], [w.index for w in ws])

        ws = self.c.wells_from("B3", 6)
        self.assertEqual([7, 8, 9, 10, 11, 12], [w.index for w in ws])

        ws = self.c.wells_from("A1", 6, columnwise=True)
        self.assertEqual([0, 5, 10, 1, 6, 11], [w.index for w in ws])

        ws = self.c.wells_from("B3", 6, columnwise=True)
        self.assertEqual([7, 12, 3, 8, 13, 4], [w.index for w in ws])

        with self.assertRaises(TypeError):
            self.c.wells_from(["unexpected collection"], 4)
        with self.assertRaises(TypeError):
            self.c.wells_from("B3", 3.14)

    def test_setter_typechecking(self):
        ws = self.c.all_wells()
        with self.assertRaises(TypeError):
            ws.set_properties(["not", "a", "dictionary"])
        with self.assertRaises(TypeError):
            ws.set_volume(200)

    def test_append(self):
        another_container = Container(None, dummy_type)
        ws = self.c.all_wells()
        self.assertEqual(15, len(ws))
        ws.append(another_container.well(0))
        self.assertEqual(16, len(ws))
        with self.assertRaises(TypeError):
            ws.append("not a well")

    def test_extend(self):
        another_container = Container(None, dummy_type)
        ws = self.c.all_wells()
        self.assertEqual(15, len(ws))
        ws.extend(another_container.all_wells())
        self.assertEqual(30, len(ws))
        with self.assertRaises(TypeError):
            ws.extend(another_container.well(0))

    def test_add(self):
        ws = self.c.all_wells()
        self.assertEqual(15, len(ws))
        another_container = Container(None, dummy_type)
        ws_bigger = self.c.all_wells() + another_container.all_wells()
        self.assertEqual(30, len(ws_bigger))
        ws_plus_well = ws + another_container.well(0)
        self.assertEqual(16, len(ws_plus_well))
        with self.assertRaises(TypeError):
            ws = ws + "not a well"

    def test_quadrant(self):
        def create_container(container_type):
            return Container(None, container_type)

        plate_96 = create_container(
            make_dummy_type(well_count=96, col_count=12))
        plate_384 = create_container(
            make_dummy_type(well_count=384, col_count=24))
        plate_1536 = create_container(
            make_dummy_type(well_count=1536, col_count=48))
        pathological_plate = create_container(
            make_dummy_type(well_count=384, col_count=96))

        for plate in plate_96, plate_384:
            ws = plate.quadrant(0)
            self.assertEqual(96, len(ws))
            self.assertIsInstance(ws, WellGroup)

        quadB1 = plate_384.quadrant("B1")
        self.assertEqual(96, len(quadB1))
        self.assertEqual(24, quadB1[0].index)
        self.assertEqual(26, quadB1[1].index)

        # unsupported plate geometries
        for plate in plate_1536, pathological_plate:
            with self.assertRaises(ValueError):
                plate.quadrant(0)

        # bogus quadrants
        with self.assertRaises(ValueError):
            plate_96.quadrant("B2")

        with self.assertRaises(ValueError):
            plate_384.quadrant(9)


class WellVolumeTestCase(unittest.TestCase):

    def test_set_volume(self):
        c = Container(None, dummy_type)
        c.well(0).set_volume("20:microliter")
        self.assertEqual(Unit(20, "microliter"), c.well(0).volume)
        self.assertEqual("microliter", c.well(0).volume.unit)
        self.assertIs(None, c.well(1).volume)

    def test_set_volume_through_group(self):
        c = Container(None, dummy_type)
        c.all_wells().set_volume("30:microliter")
        for w in c.all_wells():
            self.assertEqual(Unit(30, "microliter"), w.volume)

    def test_set_volume_unit_conv(self):
        c = Container(None, dummy_type)
        c.well(0).set_volume("200:nanoliter")
        self.assertTrue(c.well(0).volume == Unit(0.2, "microliter"))
        c.well(1).set_volume(".1:milliliter")
        self.assertTrue(c.well(1).volume == Unit(100, "microliter"))
        with self.assertRaises(ValueError):
            c.well(2).set_volume("1:milliliter")


class WellPropertyTestCase(unittest.TestCase):

    def test_set_properties(self):
        c = Container(None, dummy_type)
        c.well(0).set_properties({"Concentration": "40:nanogram/microliter"})
        self.assertIsInstance(c.well(0).properties, dict)
        self.assertEqual(["Concentration"],
                         list(c.well(0).properties.keys()))
        self.assertEqual(["40:nanogram/microliter"],
                         list(c.well(0).properties.values()))
        c.well(0).set_properties({"Dilution": "1"})
        self.assertEqual(["Dilution"],
                         list(c.well(0).properties.keys()))
        self.assertEqual(["1"],
                         list(c.well(0).properties.values()))
        self.assertRaises(TypeError, c.well(0).set_properties,
                          ["property", "value"])

    def test_add_properties(self):
        c = Container(None, dummy_type)
        c.well(0).add_properties({"nickname": "dummy"})
        self.assertEqual(len(c.well(0).properties.keys()), 1)
        c.well(0).add_properties({"nickname": "dummy2"})
        self.assertEqual(len(c.well(0).properties.keys()), 1)
        self.assertEqual(["dummy2"],
                         list(c.well(0).properties.values()))
        c.well(0).set_properties({"concentration": "12:nanogram/microliter"})
        self.assertEqual(len(c.well(0).properties.keys()), 2)
        c.well(0).add_properties({"property1": "2", "ratio": "1:10"})
        self.assertEqual(len(c.well(0).properties.keys()), 4)
        self.assertRaises(TypeError, c.well(0).add_properties,
                          ["property", "value"])

    def test_properties_copy(self):
        c = Container(None, dummy_type)
        c.well(0).set_properties({"Concentration": "40:nanogram/microliter"})
        c2 = Container(None, dummy_type)
        c2.well(0).set_properties(c.well(0).properties)
        c2.well(0).add_properties({"nickname": "dummy"})
        self.assertEqual(["Concentration"],
                         list(c.well(0).properties.keys()))
        self.assertEqual(["40:nanogram/microliter"],
                         list(c.well(0).properties.values()))
        c2.well(0).set_properties({"nickname": "dummy"})
        self.assertEqual(["Concentration"],
                         list(c.well(0).properties.keys()))
        self.assertEqual(["40:nanogram/microliter"],
                         list(c.well(0).properties.values()))

    def test_add_properties_wellgroup(self):
        c = Container(None, dummy_type)
        group = c.wells_from(0, 3).set_properties({"property1": "value1",
                                                   "property2": "value2"})
        c.well(0).add_properties({"property4": "value4"})
        self.assertEqual(len(c.well(0).properties.keys()), 3)
        for well in group:
            self.assertTrue("property1" in well.properties)
            self.assertTrue("property2" in well.properties)


class WellNameTestCase(unittest.TestCase):

    def test_set_name(self):
        c = Container(None, dummy_type)
        c.well(0).set_name("sample")
        self.assertEqual(c.well(0).name, "sample")


class WellGroupNameTestCase(unittest.TestCase):

    def setUp(self):
        self.c = Container(None, dummy_type)

    def test_set_group_name(self):
        ws = self.c.all_wells()
        ws.set_group_name("test_name")
        self.assertEqual(ws.name, "test_name")


class WellGroupListTestCase(unittest.TestCase):

    def setUp(self):
        self.c = Container(None, dummy_type)

    def test_wells_with(self):
        ws = self.c.wells_from('A1', 2)
        ws.set_properties({'property1': 'value1'})
        prop = ws.wells_with('property1')
        self.assertTrue("property1" in prop[0].properties)
        self.assertTrue("property1" in prop[1].properties)
        ws2 = self.c.wells_from('B1', 2)
        ws2.set_properties({'property2': 'value2'})
        ws.extend(ws2)
        self.assertTrue("property1" not in ws[2].properties)
        self.assertTrue("property1" not in ws[3].properties)
        self.assertTrue("property2" in ws[2].properties)
        self.assertTrue("property2" in ws[3].properties)
        ws[2].set_properties({'property1': 'value2'})
        ws[3].set_properties({'property1': 'value2'})
        prop = ws.wells_with('property1')
        self.assertTrue(len(prop) == 4)
        prop_and_val = ws.wells_with('property1', 'value2')
        self.assertTrue(prop_and_val[0] == ws[2])
        self.assertTrue(prop_and_val[1] == ws[3])

    def test_pop(self):
        ws = self.c.wells_from('A1', 3)
        self.assertTrue(ws[0] == ws.pop(0))
        self.assertEqual(ws[-1], ws.pop())
        self.assertEqual(len(ws), 1)
        self.assertEqual(ws[-1], ws.pop())
        self.assertEqual(len(ws), 0)

    def test_insert(self):
        ws = self.c.wells('A1', 2)
        insert_wells = self.c.wells_from('C1', 3)
        ws.insert(1, insert_wells[0])
        self.assertEqual(ws[1], insert_wells[0])
        ws.insert(0, insert_wells[1])
        self.assertEqual(ws[0], insert_wells[1])
        ws.insert(100, insert_wells[2])
        self.assertTrue(ws[-1] == insert_wells[2])
        self.assertTrue(len(ws) == 5)
