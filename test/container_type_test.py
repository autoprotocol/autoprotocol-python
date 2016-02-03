import unittest
from autoprotocol.container_type import ContainerType
from autoprotocol.container import Container

dummy_type = ContainerType(name="dummy",
                           well_count=15,
                           well_depth_mm=None,
                           well_volume_ul=200,
                           well_coating=None,
                           sterile=False,
                           is_tube=False,
                           capabilities=[],
                           shortname="dummy",
                           col_count=5,
                           dead_volume_ul=15)

class ContainerRobotizeTestCase(unittest.TestCase):
    def test_robotize_decompose(self):
      for ref in ["a1", "A1", "0", 0]:
          self.assertEqual(0, dummy_type.robotize(ref))
          self.assertEqual((0, 0), dummy_type.decompose(ref))
      for ref in ["a5", "A5", "4", 4]:
          self.assertEqual(4, dummy_type.robotize(ref))
          self.assertEqual((0, 4), dummy_type.decompose(ref))
      for ref in ["b1", "B1", "5", 5]:
          self.assertEqual(5, dummy_type.robotize(ref))
          self.assertEqual((1, 0), dummy_type.decompose(ref))
      for ref in ["c5", "C5", "14", 14]:
          self.assertEqual(14, dummy_type.robotize(ref))
          self.assertEqual((2, 4), dummy_type.decompose(ref))

    def test_robotize_decompose_checks(self):
        for ref in [["A1", "B1"], 1.0]:
            with self.assertRaises(TypeError):
                dummy_type.robotize(ref)
            with self.assertRaises(TypeError):
                dummy_type.decompose(ref)
        for ref in ["D1", "A6", 15, "2A2"]:
            with self.assertRaises(ValueError):
                dummy_type.robotize(ref)
            with self.assertRaises(ValueError):
                dummy_type.decompose(ref)

    def test_humanize(self):
      self.assertEqual("A1", dummy_type.humanize(0))
      self.assertEqual("A5", dummy_type.humanize(4))
      self.assertEqual("B2", dummy_type.humanize(6))
      self.assertEqual("C5", dummy_type.humanize(14))
      with self.assertRaises(ValueError):
        dummy_type.humanize(15)
      with self.assertRaises(TypeError):
        dummy_type.humanize("A1")
