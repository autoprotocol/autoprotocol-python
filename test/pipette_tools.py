
import unittest

from autoprotocol import pipette_tools, protocol

class PipetteToolsTestCase(unittest.TestCase):
    def test_aspirate_source(self):
        depth = pipette_tools.depth(
            "ll_surface",
            distance="0.0:meter",
        )
        speed = {
            "start": "50:microliter/second",
            "max": "150:microliter/second"
        }

        self.assertEqual(
            pipette_tools.aspirate_source(
                depth=depth,
                aspirate_speed=speed,
                cal_volume="100 microliter",
                primer_vol="10 microliter",
            ),
            {
                "depth": depth,
                "aspirate_speed": speed,
                "volume": "100 microliter",
                "primer_vol": "10 microliter",
            },
        )


    def test_dispense_target(self):
        depth = pipette_tools.depth(
            "ll_surface",
            distance="0.0:meter",
        )
        speed = {
            "start": "50:microliter/second",
            "max": "150:microliter/second"
        }

        self.assertEqual(
            pipette_tools.dispense_target(
                depth=depth,
                dispense_speed=speed,
                cal_volume="100 microliter",
            ),
            {
                "depth": depth,
                "dispense_speed": speed,
                "volume": "100 microliter",
            },
        )


    def test_distribute_target(self):
        depth = pipette_tools.depth(
            "ll_surface",
            distance="0.0:meter",
        )
        speed = {
            "start": "50:microliter/second",
            "max": "150:microliter/second"
        }
        p = protocol.Protocol()
        sample_plate = p.ref("sample", None, "96-pcr", discard=True)
        target = pipette_tools.dispense_target(
            depth=pipette_tools.depth("ll_surface"),
        )

        self.assertEqual(
            pipette_tools.distribute_target(
                sample_plate.well(1),
                "100 microliter",
                dispense_speed=speed,
                dispense_target=target,
            ),
            {
                "well": sample_plate.well(1),
                "volume": "100 microliter",
                "dispense_speed": speed,
                "x_dispense_target": target,
            },
        )

    def test_depth(self):
        self.assertEqual(
            pipette_tools.depth(
                "ll_surface",
                distance="0.0:meter",
            ),
            {
                "method": "ll_surface",
                "distance": "0.0:meter",
            },
        )


    def test_assign(self):
        obj = {}
        pipette_tools.assign(obj, "key", 1)
        pipette_tools.assign(obj, "no_key", None)

        self.assertEqual(
            obj["key"],
            1,
        )

        self.assertNotIn(
            "no_key",
            obj,
        )
