# pragma pylint: disable=missing-docstring, no-self-use, invalid-name
# pragma pylint: disable=too-few-public-methods, attribute-defined-outside-init
# pragma pylint: disable=protected-access
from contextlib import contextmanager
from functools import reduce

import pytest

from autoprotocol import Container, ContainerType, Protocol, Well, WellGroup
from autoprotocol.instruction import LiquidHandle
from autoprotocol.liquid_handle.dispense import Dispense as DispenseMethod
from autoprotocol.liquid_handle.liquid_class import LiquidClass
from autoprotocol.unit import Unit


class ProteinBuffer(LiquidClass):
    def __init__(self):
        super(ProteinBuffer, self).__init__()
        self.name = "protein_buffer"


class TestDispenseMethod(DispenseMethod):
    def __init__(self):
        super(TestDispenseMethod, self).__init__()
        self._liquid = ProteinBuffer()


def dummy_tube_well(name="dummy"):
    return (
        Container(
            None,
            ContainerType(
                name="dummy",
                well_count=1,
                well_depth_mm=None,
                well_volume_ul=Unit(50, "milliliter"),
                well_coating=None,
                sterile=False,
                is_tube=True,
                cover_types=[],
                seal_types=None,
                capabilities=[],
                shortname="dummy",
                col_count=1,
                dead_volume_ul=Unit(3, "milliliter"),
                safe_min_volume_ul=Unit(2, "milliliter"),
            ),
            name=name,
        )
        .well(0)
        .set_volume("50:milliliter")
    )


@contextmanager
def does_not_raise():
    yield


class LiquidHandleTester(object):
    @pytest.fixture(autouse=True, scope="function")
    def protocol(self):
        yield Protocol()

    @pytest.fixture(autouse=True, scope="function")
    def setup(self, protocol, dummy_96):
        self.protocol = protocol
        self.src_tube_1: Well = dummy_tube_well()
        self.src_tube_2: Well = dummy_tube_well()
        self.src_tube_3: Well = dummy_tube_well()
        self.flat = dummy_96
        self.test_volume = "100:uL"
        self.rows = 8
        self.columns = 1
        self.liquid = ProteinBuffer()
        self.method = TestDispenseMethod()
        self.shape = LiquidHandle.builders.shape(self.rows, self.columns, None)


class TestLiquidHandleUserConfig(LiquidHandleTester):
    def test_source_configuration(self):
        test_input_types = [
            (does_not_raise(), self.src_tube_1),
            (does_not_raise(), [(self.src_tube_1, 1)]),
            (pytest.raises(ValueError), [(self.src_tube_1, "1")]),
            (pytest.raises(ValueError), [self.src_tube_1, 1]),
        ]
        destination = self.flat.well(1)
        volume = self.test_volume
        for expectation, test_input_type in test_input_types:
            with expectation:
                self.protocol.liquid_handle_dispense(
                    source=test_input_type, destination=destination, volume=volume
                )

    def test_destination_configuration(self):
        # Destinations must match the number of chips specified in the source tuple
        source = [(self.src_tube_1, 2), (self.src_tube_2, 1)]
        test_input_types = [
            (does_not_raise(), [self.flat.wells_from(0, 2), self.flat.well(3)]),
            (does_not_raise(), [self.flat.wells_from(0, 2)]),
            (does_not_raise(), self.flat.wells_from(0, 2)),
            (
                does_not_raise(),
                [[self.flat.well(0), self.flat.well(1)], self.flat.well(0)],
            ),
            (
                does_not_raise(),
                [
                    [self.flat.well(0), self.flat.well(1), self.flat.well(2)],
                    self.flat.well(0),
                ],
            ),
            (does_not_raise(), [self.flat.well(0), self.flat.well(1)]),
            (does_not_raise(), [self.flat.well(1)]),
            (does_not_raise(), self.flat.well(1)),
        ]
        volume = self.test_volume
        for expectation, test_input_type in test_input_types:
            with expectation:
                self.protocol.liquid_handle_dispense(
                    source=source, destination=test_input_type, volume=volume
                )

    def test_volume_configuration(self):
        test_input_types = [
            (does_not_raise(), "3:ul"),
            (does_not_raise(), Unit("4:ul")),
            (does_not_raise(), [Unit("5:ul")]),
            (does_not_raise(), [[Unit("6:ul")], [Unit("7:ul")]]),
            (does_not_raise(), ["8:ul", "9:ul"]),
            (pytest.raises(ValueError), ["10:ul", "11:ul", "12:ul"]),
            (pytest.raises(TypeError), [["13:ul", "14:ul", "15:ul"]]),
            (pytest.raises(ValueError), [["16:ul", "17:ul", "18:ul"], ["19:ul"]]),
        ]
        source = [(self.src_tube_1, 1), (self.src_tube_2, 1)]
        destination = [self.flat.well(0), self.flat.well(1)]
        for expectation, test_input_type in test_input_types:
            with expectation:
                self.protocol.liquid_handle_dispense(
                    source=source, destination=destination, volume=test_input_type
                )

    def test_liquid_class_configuration(self):
        test_input_types = [
            (does_not_raise(), LiquidClass()),
            (does_not_raise(), ProteinBuffer()),
            (does_not_raise(), [LiquidClass(), LiquidClass()]),
            (pytest.raises(ValueError), [LiquidClass(), LiquidClass(), LiquidClass()]),
        ]
        source = [(self.src_tube_1, 1), (self.src_tube_2, 1)]
        destination = [self.flat.well(0), self.flat.well(1)]
        volume = ["42:ul", "42:ul"]
        for expectation, test_input_type in test_input_types:
            with expectation:
                self.protocol.liquid_handle_dispense(
                    source=source,
                    destination=destination,
                    volume=volume,
                    liquid=test_input_type,
                )

    def test_dispense_method_configuration(self):
        test_input_types = [
            (does_not_raise(), DispenseMethod()),
            (does_not_raise(), TestDispenseMethod()),
            (does_not_raise(), [DispenseMethod(), DispenseMethod()]),
            (
                pytest.raises(ValueError),
                [DispenseMethod(), DispenseMethod(), DispenseMethod()],
            ),
        ]
        source = [self.src_tube_1, self.src_tube_2]
        destination = [self.flat.well(0), self.flat.well(1)]
        volume = ["42:ul", "42:ul"]
        liquid = [LiquidClass(), LiquidClass()]
        for expectation, test_input_type in test_input_types:
            with expectation:
                self.protocol.liquid_handle_dispense(
                    source=source,
                    destination=destination,
                    volume=volume,
                    liquid=liquid,
                    method=test_input_type,
                )


class TestLiquidHandleMultiDispenseMode:
    """Test using multiple hoses in one tube that will dispense to multiple columns at once"""

    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        self.protocol = Protocol()
        self.src_tube_1: Well = dummy_tube_well()
        self.src_tube_2: Well = dummy_tube_well()
        self.src_tube_3: Well = dummy_tube_well()
        self.src_tube_1.set_volume("50:microliter")
        self.src_tube_2.set_volume("50:microliter")
        self.src_tube_3.set_volume("50:microliter")
        self.reagent_name_1 = "reagent_name_1"
        self.reagent_name_2 = "reagent_name_2"
        self.reagent_name_3 = "reagent_name_3"
        self.flat = self.protocol.ref("flat", cont_type="96-flat", discard=True)
        self.test_volume = "100:uL"
        self.rows = 8
        self.columns = 1
        self.liquid = ProteinBuffer()
        self.method = TestDispenseMethod()
        self.shape = LiquidHandle.builders.shape(self.rows, self.columns, None)

    @pytest.mark.parametrize("num_chips", [1, 6, 12, 13])
    @pytest.mark.parametrize("source_tube", [dummy_tube_well()])
    def test_max_number_of_chips(
        self, num_chips, source_tube, default_max_num_dispense_chips=12
    ):
        source = [(source_tube, num_chips)]
        initial_src_volume = source_tube.volume
        destination = self.flat.wells_from(0, num_chips)
        total_volume_dispensed: Unit = Unit("0:microliter")

        if num_chips > default_max_num_dispense_chips:
            with pytest.raises(ValueError):
                self.protocol.liquid_handle_dispense(
                    source=source,
                    destination=destination,
                    volume=self.test_volume,
                    liquid=self.liquid,
                    method=self.method,
                )
        else:
            self.protocol.liquid_handle_dispense(
                source=source,
                destination=destination,
                volume=self.test_volume,
                liquid=self.liquid,
                method=self.method,
            )
            instr = self.protocol.instructions[-1]
            # Vol dispensed to destination
            total_volume_dispensed += sum(
                [
                    self.rows * self.columns * Unit(vol)
                    for vol in [self.test_volume] * len(destination)
                ]
            )
            # Vol dispensed in predispense
            total_volume_dispensed += (
                self.method.get_predispense_volume()
                * self.rows
                * self.columns
                * num_chips
            )

            source_loc = instr.locations[0]
            assert source_loc["location"] == source_tube
            assert len(source_loc["transports"]) == num_chips
            assert source_tube.volume == initial_src_volume - total_volume_dispensed

            priming_loc = instr.locations[1]
            assert priming_loc["location"] == source_tube
            assert len(priming_loc["transports"]) == num_chips

            predispense_loc = instr.locations[2]
            assert predispense_loc.get("location") == None
            assert len(predispense_loc["transports"]) == num_chips

            for i, dest_well in enumerate(destination):
                destination_loc = instr.locations[3 + i]
                assert destination_loc["location"] == dest_well
                assert len(destination_loc["transports"]) == 1

            filled_destinations = list(
                reduce(
                    lambda a, b: a + b,
                    [
                        self.flat.wells_from_shape(dest_well.index, self.shape).wells
                        for dest_well in destination
                    ],
                )
            )
            assert all(w.volume == Unit(self.test_volume) for w in filled_destinations)

    def test_num_chips_vs_num_destinations(self):
        """Test number of chips >, =, and < number of destinations"""
        test_input_types = [
            (does_not_raise(), [4, [self.flat.well(0)]]),
            (does_not_raise(), [1, [self.flat.well(2)]]),
            (does_not_raise(), [1, [self.flat.well(3), self.flat.well(4)]]),
        ]
        for expectation, (num_chips, destination) in test_input_types:
            with expectation:
                source = [(self.src_tube_1, num_chips)]
                initial_src_volume = self.src_tube_1.volume

                total_volume_dispensed: Unit = Unit("0:microliter")
                self.protocol.liquid_handle_dispense(
                    source=source,
                    destination=destination,
                    volume=self.test_volume,
                    liquid=self.liquid,
                    method=self.method,
                )

                instr = self.protocol.instructions[-1]
                # Vol dispensed to destination
                total_volume_dispensed += sum(
                    [
                        self.rows * self.columns * Unit(vol)
                        for vol in [self.test_volume] * len(destination)
                    ]
                )
                # Vol dispensed in predispense
                total_volume_dispensed += (
                    self.method.get_predispense_volume()
                    * self.rows
                    * self.columns
                    * num_chips
                )

                source_loc = instr.locations[0]
                assert source_loc["location"] == self.src_tube_1
                assert len(source_loc["transports"]) == num_chips
                assert (
                    self.src_tube_1.volume
                    == initial_src_volume - total_volume_dispensed
                )

                priming_loc = instr.locations[1]
                assert priming_loc["location"] == self.src_tube_1
                assert len(priming_loc["transports"]) == num_chips

                predispense_loc = instr.locations[2]
                assert predispense_loc.get("location") == None
                assert len(predispense_loc["transports"]) == num_chips

                for i, dest_well in enumerate(destination):
                    destination_loc = instr.locations[3 + i]
                    assert destination_loc["location"] == dest_well
                    assert len(destination_loc["transports"]) == 1

                filled_destinations = list(
                    reduce(
                        lambda a, b: a + b,
                        [
                            self.flat.wells_from_shape(
                                dest_well.index, self.shape
                            ).wells
                            for dest_well in destination
                        ],
                    )
                )
                assert all(
                    w.volume == Unit(self.test_volume) for w in filled_destinations
                )

    def test_num_multi_chips_for_multiple_srcs_to_single_dest(self):
        test_input_types = [
            (
                does_not_raise(),
                [[(dummy_tube_well(), 2), (dummy_tube_well(), 2)], [self.flat.well(0)]],
            ),
            (
                does_not_raise(),
                [[(dummy_tube_well(), 2), (dummy_tube_well(), 2)], [self.flat.well(2)]],
            ),
            (
                does_not_raise(),
                [[(dummy_tube_well(), 2), (dummy_tube_well(), 2)], [self.flat.well(3)]],
            ),
        ]
        for expectation, (source, destination) in test_input_types:
            with expectation:
                # source = [(self.src_tube_1, num_chips)]
                src_tube_1, num_chip_1 = source[0]
                src_tube_2, num_chip_2 = source[1]
                initial_src_volume_1 = src_tube_1.volume
                initial_src_volume_2 = src_tube_2.volume

                total_volume_dispensed_1: Unit = Unit("0:microliter")
                total_volume_dispensed_2: Unit = Unit("0:microliter")
                self.protocol.liquid_handle_dispense(
                    source=source,
                    destination=destination,
                    volume=self.test_volume,
                    liquid=self.liquid,
                    method=self.method,
                )

                instr = self.protocol.instructions[-1]
                # Vol dispensed to destination
                total_volume_dispensed_1 += sum(
                    [
                        self.rows
                        * self.columns
                        * Unit(self.test_volume)
                        * len(destination)
                    ]
                )
                # Vol dispensed in predispense
                total_volume_dispensed_1 += (
                    self.method.get_predispense_volume()
                    * self.rows
                    * self.columns
                    * num_chip_1
                )

                total_volume_dispensed_2 += sum(
                    [
                        self.rows
                        * self.columns
                        * Unit(self.test_volume)
                        * len(destination)
                    ]
                )
                # Vol dispensed in predispense
                total_volume_dispensed_2 += (
                    self.method.get_predispense_volume()
                    * self.rows
                    * self.columns
                    * num_chip_2
                )
                loc_slices, src_count = [], None
                for loc in instr.locations:
                    if loc["transports"][0]["volume"] < Unit("0:microliter"):
                        loc_slices.append([])
                        if src_count is None:
                            src_count = 0
                        else:
                            src_count += 1
                    loc_slices[src_count].append(loc)

                dispensed_volumes = [
                    (initial_src_volume_1, total_volume_dispensed_1),
                    (initial_src_volume_2, total_volume_dispensed_2),
                ]
                for (
                    locations,
                    (src_tube, num_chip),
                    (initial_src_volume, total_volume_dispensed),
                ) in zip(loc_slices, source, dispensed_volumes):

                    source_loc = locations[0]
                    assert source_loc["location"] == src_tube
                    assert len(source_loc["transports"]) == num_chip
                    assert (
                        src_tube.volume == initial_src_volume - total_volume_dispensed
                    )

                    priming_loc = locations[1]
                    assert priming_loc["location"] == src_tube
                    assert len(priming_loc["transports"]) == num_chip

                    predispense_loc = locations[2]
                    assert predispense_loc.get("location") == None
                    assert len(predispense_loc["transports"]) == num_chip

                    for i, dest_well in enumerate(destination):
                        destination_loc = locations[3 + i]
                        assert destination_loc["location"] == dest_well
                        assert len(destination_loc["transports"]) == 1
                    filled_destinations = list(
                        reduce(
                            lambda a, b: a + b,
                            [
                                self.flat.wells_from_shape(
                                    dest_well.index, self.shape
                                ).wells
                                for dest_well in destination
                            ],
                        )
                    )
                    # Sources are dispensing to the same destination
                    assert all(
                        w.volume == Unit(self.test_volume) * len(source)
                        for w in filled_destinations
                    )

    def test_num_multi_chips_for_multiple_srcs_to_multi_dest(self):
        test_input_types = [
            (
                does_not_raise(),
                [
                    [(dummy_tube_well("src1"), 3), (dummy_tube_well("src2"), 2)],
                    [[self.flat.well(0), self.flat.well(1)]],
                ],
            ),
        ]
        for expectation, (source, destination) in test_input_types:
            with expectation:
                # source = [(self.src_tube_1, num_chips)]
                src_tube_1, num_chip_1 = source[0]
                src_tube_2, num_chip_2 = source[1]
                initial_src_volume_1 = src_tube_1.volume
                initial_src_volume_2 = src_tube_2.volume

                total_volume_dispensed_1: Unit = Unit("0:microliter")
                total_volume_dispensed_2: Unit = Unit("0:microliter")
                self.protocol.liquid_handle_dispense(
                    source=source,
                    destination=destination,
                    volume=self.test_volume,
                    liquid=self.liquid,
                    method=self.method,
                )
                destination = destination[0]
                instr = self.protocol.instructions[-1]
                # Vol dispensed to destination
                dispensed_vols = [self.test_volume for w in [wg for wg in destination]]
                total_volume_dispensed_1 += sum(
                    [self.rows * self.columns * Unit(vol) for vol in dispensed_vols]
                )
                # Vol dispensed in predispense
                total_volume_dispensed_1 += (
                    self.method.get_predispense_volume()
                    * self.rows
                    * self.columns
                    * num_chip_1
                )

                total_volume_dispensed_2 += sum(
                    [self.rows * self.columns * Unit(vol) for vol in dispensed_vols]
                )

                # Vol dispensed in predispense
                total_volume_dispensed_2 += (
                    self.method.get_predispense_volume()
                    * self.rows
                    * self.columns
                    * num_chip_2
                )

                loc_slices, src_count = [], None
                for loc in instr.locations:
                    if loc["transports"][0]["volume"] < Unit("0:microliter"):
                        loc_slices.append([])
                        if src_count is None:
                            src_count = 0
                        else:
                            src_count += 1
                    loc_slices[src_count].append(loc)

                loc_list = []
                loc_idx = 0
                src_dest_pairs = 0
                while loc_idx < len(instr.locations):
                    loc = instr.locations[loc_idx]
                    if loc["transports"][0]["volume"] < Unit("0:microliter"):
                        loc_list.append(
                            {
                                "src": loc["location"],
                                "num_chips": len(loc["transports"]),
                                "destinations": [],
                                "priming_loc": instr.locations[loc_idx + 1],
                                "predispense_loc": instr.locations[loc_idx + 2],
                            }
                        )
                        src_dest_pairs += 1
                        loc_idx += 3
                    else:
                        loc_list[src_dest_pairs - 1]["destinations"].append(loc)
                        loc_idx += 1

                dispensed_volumes = [
                    (initial_src_volume_1, total_volume_dispensed_1),
                    (initial_src_volume_2, total_volume_dispensed_2),
                ]

                for (
                    (location_info),
                    (src_tube, num_chip),
                    (initial_src_volume, total_volume_dispensed),
                ) in zip(loc_list, source, dispensed_volumes):
                    assert location_info["src"] == src_tube
                    assert location_info["num_chips"] == num_chip
                    assert (
                        src_tube.volume == initial_src_volume - total_volume_dispensed
                    )

                    assert location_info["priming_loc"]["location"] == src_tube
                    assert len(location_info["priming_loc"]["transports"]) == num_chip

                    assert location_info["predispense_loc"].get("location") == None
                    assert (
                        len(location_info["predispense_loc"]["transports"]) == num_chip
                    )

                    for i, dest_well in enumerate(destination):
                        destination_loc = location_info["destinations"][i]
                        assert destination_loc["location"] == dest_well
                        assert len(destination_loc["transports"]) == 1

                        destination_loc = location_info["destinations"][i]
                        assert destination_loc["location"] == dest_well
                        assert len(destination_loc["transports"]) == 1
                    filled_destinations = list(
                        reduce(
                            lambda a, b: a + b,
                            [
                                self.flat.wells_from_shape(
                                    dest_well.index, self.shape
                                ).wells
                                for dest_well in destination
                            ],
                        )
                    )
                    # Sources are dispensing to the same destination
                    assert all(
                        w.volume == Unit(self.test_volume) * len(destination)
                        for w in filled_destinations
                    )


class TestLiquidHandleDispenseMode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.protocol = Protocol()
        self.tube = self.protocol.ref("tube", cont_type="micro-2.0", discard=True)
        self.tube.well(0).set_volume("50:microliter")
        self.flat = self.protocol.ref("flat", cont_type="96-flat", discard=True)

    def test_location_count(self):
        volume = "5:uL"
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.wells_from(0, 12),
            volume=volume,
        )
        assert self.protocol.instructions[-1].op == "liquid_handle"
        assert len(instruction.data["locations"]) == 15

    def test_source_params(self):
        source = self.tube.well(0)
        destinations = self.flat.wells_from(0, 12)
        dispense_vol = Unit(10, "uL")
        aspirate_vol = -(
            DispenseMethod.default_prime()
            + DispenseMethod.default_predispense()
            + dispense_vol * len(destinations)
        )
        instruction = self.protocol.liquid_handle_dispense(
            source=source, destination=destinations, volume=dispense_vol
        )
        aspirate_location = {
            "location": source,
            "transports": [{"volume": aspirate_vol, "mode_params": {}}],
        }

        assert instruction.data["locations"][0] == aspirate_location

    def test_prime_params(self):
        source = self.tube.well(0)
        prime_vol = Unit(100, "uL")
        instruction = self.protocol.liquid_handle_dispense(
            source=source,
            destination=self.flat.well(0),
            volume="5:uL",
            method=DispenseMethod(prime=prime_vol),
        )
        prime_location = {
            "location": source,
            "transports": [{"volume": prime_vol, "mode_params": {}}],
        }

        assert instruction.data["locations"][1] == prime_location

    def test_no_auxiliary_dispenses(self):
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=WellGroup([]),
            volume="5:uL",
            method=DispenseMethod(prime=False, predispense=False),
        )

        assert len(instruction.data["locations"]) == 1

    def test_predispense_params(self):
        source = self.tube.well(0)
        predispense_vol = Unit(100, "uL")
        instruction = self.protocol.liquid_handle_dispense(
            source=source,
            destination=self.flat.well(0),
            volume="5:uL",
            method=DispenseMethod(predispense=predispense_vol),
        )
        predispense_location = {
            "transports": [{"volume": predispense_vol, "mode_params": {}}]
        }

        assert instruction.data["locations"][2] == predispense_location

    def test_destination_params(self):
        destinations = self.flat.wells_from(0, 12)
        volume = Unit(5, "uL")
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0), destination=destinations, volume=volume
        )

        destination_locations = instruction.data["locations"][3:]
        for dest, location in zip(destinations, destination_locations):
            dest_location = {
                "location": dest,
                "transports": [{"volume": volume, "mode_params": {}}],
            }
            assert location == dest_location

    def test_volume_resolution_propagation(self):
        destination = self.flat.well(0)
        volume_resolution = Unit(1, "uL")
        volume = Unit(5, "uL")
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=destination,
            volume=volume,
            method=DispenseMethod(volume_resolution=volume_resolution),
        )
        destination_location = {
            "location": destination,
            "transports": [
                {
                    "volume": volume,
                    "mode_params": {"volume_resolution": volume_resolution},
                }
            ],
        }

        assert instruction.data["locations"][3] == destination_location

    def test_liquid_class_propagation(self):
        liquid_class = "protein_buffer"

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
        )

        transports = [loc.get("transports") for loc in instruction.data["locations"]]
        for transport in [item for sublist in transports for item in sublist]:
            assert transport["mode_params"]["liquid_class"] == liquid_class

    def test_tempest_chip_defaults(self):

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
        )

        assert "mode_params" not in instruction.data

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
            chip_material="silicone",
        )

        mode_params = {
            "x_tempest_chip": {
                "material": "silicone",
            }
        }

        liha_shape = instruction.data["shape"]
        assert liha_shape["rows"] == 8 and liha_shape["columns"] == 1
        assert instruction.data["mode_params"] == mode_params

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
            model="high_volume",
            chip_material="silicone",
            nozzle="standard",
        )

        mode_params = {
            "x_tempest_chip": {
                "model": "high_volume",
                "material": "silicone",
                "nozzle": "standard",
            }
        }

        assert instruction.data["mode_params"] == mode_params

    def test_tempest_chip_pfe(self):

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
            chip_material="pfe",
        )

        mode_params = {
            "x_tempest_chip": {
                "material": "pfe",
            }
        }

        liha_shape = instruction.data["shape"]
        assert liha_shape["rows"] == 8 and liha_shape["columns"] == 1
        assert instruction.data["mode_params"] == mode_params

    def test_tempest_bad_chip_param(self):

        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                liquid=ProteinBuffer,
                chip_material="abc",
            )
        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                liquid=ProteinBuffer,
                model="low_volume",
            )

        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                liquid=ProteinBuffer,
                nozzle="unique",
            )

        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                liquid=ProteinBuffer,
                model="abc",
                chip_material="xyz",
                nozzle="standard",
            )

        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                liquid=ProteinBuffer,
                model="high_volume",
                chip_material="xyz",
                nozzle="abc",
            )

    def test_mantis_default_params(self):
        """Tests mantis default params"""
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
        )

        assert "mode_params" not in instruction.data

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            rows=1,
            columns=1,
            liquid=ProteinBuffer,
            device="x_mantis",
            model="high_volume",
            diaphragm=0,
            nozzle_size="0.1:mm",
            tubing="LV",
            z_drop="0.0:mm",
            viscosity="1",
        )

        mode_params = {
            "x_mantis": {
                "model": "high_volume",
                "diaphragm": 0,
                "nozzle_size": "0.1:mm",
                "tubing": "LV",
                "z_drop": "0.0:mm",
                "viscosity": "1",
            }
        }

        liha_shape = instruction.data["shape"]
        assert liha_shape["rows"] == 1 and liha_shape["columns"] == 1
        assert instruction.data["mode_params"] == mode_params

    def test_mantis_other_params(self):
        """Tests mantis low_volume params, still accepted"""
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            rows=1,
            columns=1,
            liquid=ProteinBuffer,
            device="x_mantis",
            model="low_volume",
            diaphragm=25,
            nozzle_size="0.1:mm",
            tubing="P200",
            z_drop="0.2:mm",
            viscosity="1",
        )

        mode_params = {
            "x_mantis": {
                "model": "low_volume",
                "diaphragm": 25,
                "nozzle_size": "0.1:mm",
                "tubing": "P200",
                "z_drop": "0.2:mm",
                "viscosity": "1",
            }
        }

        liha_shape = instruction.data["shape"]
        assert liha_shape["rows"] == 1 and liha_shape["columns"] == 1
        assert instruction.data["mode_params"] == mode_params

    def test_p200_shortname_params(self):
        """Tests that pipette-tip-p200 is still accepted"""
        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            rows=1,
            columns=1,
            liquid=ProteinBuffer,
            device="x_mantis",
            model="low_volume",
            diaphragm=25,
            nozzle_size="0.1:mm",
            tubing="pipette-tip-p200",
            z_drop="0.2:mm",
            viscosity="1",
        )

        mode_params = {
            "x_mantis": {
                "model": "low_volume",
                "diaphragm": 25,
                "nozzle_size": "0.1:mm",
                "tubing": "pipette-tip-p200",
                "z_drop": "0.2:mm",
                "viscosity": "1",
            }
        }

        liha_shape = instruction.data["shape"]
        assert liha_shape["rows"] == 1 and liha_shape["columns"] == 1
        assert instruction.data["mode_params"] == mode_params

    def test_mantis_bad_params(self):
        """Tests mantis bad params"""
        # Incorrect model param and incorrect liha shape
        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                liquid=ProteinBuffer,
                device="x_mantis",
                model="mid_volume",
                diaphragm=0,
                nozzle_size="0.1:mm",
                tubing="LV",
                z_drop="0.0:mm",
                viscosity="1",
            )
        # Incorrect diaphragm value
        with pytest.raises(ValueError):
            self.protocol.liquid_handle_dispense(
                source=self.tube.well(0),
                destination=self.flat.well(0),
                volume="5:uL",
                rows=1,
                columns=1,
                liquid=ProteinBuffer,
                device="x_mantis",
                model="high_volume",
                diaphragm=101,
                nozzle_size="0.1:mm",
                tubing="LV",
                z_drop="0.0:mm",
                viscosity="1",
            )
            # Incorrect nozzle_size value
            with pytest.raises(ValueError):
                self.protocol.liquid_handle_dispense(
                    source=self.tube.well(0),
                    destination=self.flat.well(0),
                    volume="5:uL",
                    rows=1,
                    columns=1,
                    liquid=ProteinBuffer,
                    device="x_mantis",
                    model="high_volume",
                    diaphragm=101,
                    nozzle_size="0.3:mm",
                    tubing="LV",
                    z_drop="0.0:mm",
                    viscosity="1",
                )
            # Incorrect tubing value
            with pytest.raises(ValueError):
                self.protocol.liquid_handle_dispense(
                    source=self.tube.well(0),
                    destination=self.flat.well(0),
                    volume="5:uL",
                    rows=1,
                    columns=1,
                    liquid=ProteinBuffer,
                    device="x_mantis",
                    model="high_volume",
                    diaphragm=101,
                    nozzle_size="0.3:mm",
                    tubing="MV",
                    z_drop="0.0:mm",
                    viscosity="1",
                )
            # Incorrect z_drop value
            with pytest.raises(ValueError):
                self.protocol.liquid_handle_dispense(
                    source=self.tube.well(0),
                    destination=self.flat.well(0),
                    volume="5:uL",
                    rows=1,
                    columns=1,
                    liquid=ProteinBuffer,
                    device="x_mantis",
                    model="high_volume",
                    diaphragm=101,
                    nozzle_size="0.3:mm",
                    tubing="LV",
                    z_drop="200.0:mm",
                    viscosity="1",
                )
            # Incorrect viscosity value
            with pytest.raises(ValueError):
                self.protocol.liquid_handle_dispense(
                    source=self.tube.well(0),
                    destination=self.flat.well(0),
                    volume="5:uL",
                    rows=1,
                    columns=1,
                    liquid=ProteinBuffer,
                    device="x_mantis",
                    model="high_volume",
                    diaphragm=101,
                    nozzle_size="0.3:mm",
                    tubing="LV",
                    z_drop="0.0:mm",
                    viscosity="100",
                )

    def test_liquid_handle_volume_tracking(self):
        self.tube.well(0).set_volume("0:microliter")

        full_row_96_well_plate_shape = {"rows": 1, "columns": 12, "format": "SBS96"}
        full_plate_destinations = self.flat.wells_from_shape(
            0, full_row_96_well_plate_shape
        )
        self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=full_plate_destinations,
            volume="300:microliter",
            liquid=ProteinBuffer,
            method=DispenseMethod(predispense="10:microliter"),
            rows=8,
            columns=1,
        )
        # 300 microliters into 96 wells = 28.8 mL, plus predispense 10 uLx 8 tips
        # negative final source volume does not cause an error, as expected
        assert self.tube.well(0).volume == Unit(-28.88, "milliliter")
        for well in self.flat.all_wells():
            assert well.volume == Unit(300, "microliter")
