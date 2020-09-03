# pragma pylint: disable=missing-docstring, no-self-use, invalid-name
# pragma pylint: disable=too-few-public-methods, attribute-defined-outside-init
import pytest
from autoprotocol.unit import Unit
from autoprotocol.protocol import Protocol
from autoprotocol.liquid_handle import Mix, DryWellTransfer


class LiquidHandleTester(object):
    @pytest.fixture(autouse=True)
    def setup(self):
        self.p = Protocol()
        self.flat = self.p.ref("flat", cont_type="96-flat", discard=True)
        self.deep = self.p.ref("deep", cont_type="96-deep", discard=True)


class TestLiquidClassTransfer(LiquidHandleTester):
    def test_generates_liquid_handle(self):
        self.p.transfer(self.flat.well(0), self.flat.well(0), "1:uL")
        assert self.p.instructions[-1].op == "liquid_handle"

    def test_updates_well_volume(self):
        source = self.flat.well(0)
        destination = self.flat.well(1)
        source_volume = Unit(30, "uL")
        volume = Unit(20, "uL")

        self.p.transfer(source.set_volume(source_volume), destination, volume)
        assert source.volume == source_volume - volume
        assert destination.volume == volume

    def test_uncover_before_transfer(self):
        self.p.cover(self.flat)
        self.p.transfer(self.flat.well(0), self.flat.well(1), "20:uL")
        assert len(self.p.instructions) == 3
        assert self.p.instructions[-2].op == "uncover"
        assert self.flat.cover is None

    def test_can_generate_multiple_instructions(self):
        num_wells = 2
        self.p.transfer(
            self.flat.wells_from(0, num_wells),
            self.flat.wells_from(2, num_wells),
            "20:uL",
        )
        assert len(self.p.instructions) == 2

    def test_generates_correct_number_of_transports(self):
        self.p.transfer(self.flat.well(0), self.flat.well(0), "25:uL")
        assert len(self.p.instructions[0].locations[0]["transports"]) == 9
        assert len(self.p.instructions[0].locations[1]["transports"]) == 9 + 10 * 2

    def test_one_tip_generates_a_single_instruction(self):
        sources = self.flat.wells_from(0, 8)
        dests = self.flat.wells_from(12, 8)

        self.p.transfer(sources, dests, "100:uL", one_tip=True)
        assert len(self.p.instructions) == 1

    def test_split_volume_transfer(self):
        self.p.transfer(self.deep.well(0), self.deep.well(1), "2000:uL")
        assert len(self.p.instructions) == 3
        volumes = [
            _.locations[1]["transports"][4]["volume"] for _ in self.p.instructions
        ]
        expected_volumes = [Unit(895, "uL"), Unit(895, "uL"), Unit(210, "uL")]

        assert volumes == expected_volumes

    def test_split_volume_wellgroup_transfer(self):
        num_wells = 8
        transfers_per_well = 3

        self.p.transfer(
            self.deep.wells_from(0, num_wells, columnwise=True),
            self.deep.wells_from(1, num_wells, columnwise=True),
            "2:mL",
        )
        assert len(self.p.instructions) == num_wells * transfers_per_well

    def test_one_tip_split_volume_wellgroup_transfer(self):
        num_wells = 8
        transfers_per_well = 3
        transports_per_transfer = 2

        self.p.transfer(
            self.deep.wells_from(0, num_wells, columnwise=True),
            self.deep.wells_from(1, num_wells, columnwise=True),
            "2:mL",
            one_tip=True,
        )
        assert len(self.p.instructions) == 1
        assert (
            len(self.p.instructions[0].locations)
            == num_wells * transfers_per_well * transports_per_transfer
        )

    def test_generates_liquid_handle_with_density(self):
        self.p.transfer(
            self.flat.well(0), self.flat.well(0), "1:uL", density=Unit(1.1, "mg/ml")
        )
        inst = self.p.instructions[-1]
        assert inst.op == "liquid_handle"
        assert inst.data["locations"][0]["transports"][4]["density"] == Unit(
            1.1, "mg/ml"
        )

    def test_generates_liquid_handle_with_mode(self):
        self.p.transfer(
            self.flat.well(0), self.flat.well(0), "1:uL", mode="positive_displacement"
        )
        inst = self.p.instructions[-1]
        assert inst.op == "liquid_handle"
        assert inst.data["mode"] == "positive_displacement"

    def test_generates_liquid_handle_without_mode(self):
        self.p.transfer(self.flat.well(0), self.flat.well(0), "1:uL", mode=None)
        inst = self.p.instructions[-1]
        assert inst.op == "liquid_handle"
        assert inst.data["mode"] == "air_displacement"


class TestLiquidClassTransferMultiChannel(LiquidHandleTester):
    def test_updates_well_volume(self):
        source_volume = Unit(30, "uL")
        volume = Unit(20, "uL")

        row_count = self.flat.container_type.row_count()
        source_origin = self.flat.well(0)
        source_wells = self.flat.wells_from(
            source_origin, row_count, columnwise=True
        ).set_volume(source_volume)
        destination_origin = self.flat.well(1)
        destination_wells = self.flat.wells_from(
            destination_origin, row_count, columnwise=True
        )

        self.p.transfer(source_origin, destination_origin, volume, rows=row_count)
        assert all(_.volume == source_volume - volume for _ in source_wells)
        assert all(_.volume == volume for _ in destination_wells)

    def test_sbs96_shape(self):
        self.p.transfer(
            self.flat.well(0), self.flat.well(0), "20:uL", rows=8, columns=12
        )
        assert self.p.instructions[-1].shape == {
            "rows": 8,
            "columns": 12,
            "format": "SBS96",
        }

    def test_sbs384_shape(self):
        flat_384 = self.p.ref("flat_384", cont_type="384-flat", discard=True)

        self.p.transfer(
            flat_384.well(0), flat_384.well(0), "10:uL", rows=16, columns=24
        )
        assert self.p.instructions[0].shape == {
            "rows": 16,
            "columns": 24,
            "format": "SBS384",
        }

    def test_fails_on_invalid_origin(self):
        with pytest.raises(ValueError):
            self.p.transfer(self.flat.well(0), self.flat.well(95), "20:uL", rows=8)

    def test_fails_on_sbs384_transfer_in_sbs96_plate(self):
        with pytest.raises(ValueError):
            self.p.transfer(
                self.flat.well(0),
                self.flat.well(0),
                "20:uL",
                rows=16,
                columns=24,
            )


class TestLiquidClassMix(LiquidHandleTester):
    def test_produces_liquid_handle(self):
        self.p.mix(self.flat.well(0), "20:uL")
        assert self.p.instructions[0].op == "liquid_handle"

    def test_doesnt_change_well_volume(self):
        well_volume = Unit(50, "uL")

        self.p.mix(self.flat.well(0).set_volume(well_volume), "20:uL")
        assert self.flat.well(0).volume == well_volume

    def test_generates_correct_number_of_transports(self):
        self.p.mix(self.flat.well(0), "20:uL")
        assert len(self.p.instructions[0].locations[0]["transports"]) == 6 + 10 * 2

    def test_processes_customizable_mix_repetitions(self):
        repetitions = 2

        self.p.mix(self.flat.well(0), "20:uL", method=Mix(repetitions=repetitions))
        assert (
            len(self.p.instructions[0].locations[0]["transports"])
            == 6 + repetitions * 2
        )


class TestExtendedLiquidHandleMethods(LiquidHandleTester):
    def test_drywell_generates_correct_number_of_transports(self):
        self.p.transfer(
            self.flat.well(0), self.flat.well(0), "25:uL", method=DryWellTransfer()
        )
        assert len(self.p.instructions[0].locations[1]["transports"]) == 6


class TestPropagatesAliquotProperties(LiquidHandleTester):
    def test_doesnt_propagate_properties_by_default(self):
        self.flat.well(0).add_properties({"propagated": True})
        self.p.transfer(self.flat.well(0), self.flat.well(1), "5:uL")
        assert not self.flat.well(1).properties

    def test_propagates_aliquot_properties(self):
        properties = {"propagated": True}
        self.p.propagate_properties = True
        self.flat.well(0).add_properties(properties)
        self.p.transfer(self.flat.well(0), self.flat.well(1), "5:uL")
        assert self.flat.well(1).properties == properties
