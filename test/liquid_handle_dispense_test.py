# pragma pylint: disable=missing-docstring, no-self-use, invalid-name
# pragma pylint: disable=too-few-public-methods, attribute-defined-outside-init
# pragma pylint: disable=protected-access
import pytest

from autoprotocol import Protocol, Unit, WellGroup
from autoprotocol.liquid_handle.liquid_class import LiquidClass
from autoprotocol.liquid_handle.dispense import Dispense as DispenseMethod

class ProteinBuffer(LiquidClass):
    def __init__(self):
        super(ProteinBuffer, self).__init__()
        self.name = "protein_buffer"


class LiquidHandleTester(object):
    @pytest.fixture(autouse=True)
    def setup(self):
        self.protocol = Protocol()
        self.tube = self.protocol.ref("tube", cont_type="micro-2.0", discard=True)
        self.tube.well(0).set_volume("50:microliter")
        self.flat = self.protocol.ref("flat", cont_type="96-flat", discard=True)


class TestLiquidHandleDispenseMode(LiquidHandleTester):
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
            DispenseMethod.default_prime(None)
            + DispenseMethod.default_predispense(None)
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
                "nozzle": "standard",
                "model": "high_volume",
            }
        }

        assert instruction.data["mode_params"] == mode_params

        instruction = self.protocol.liquid_handle_dispense(
            source=self.tube.well(0),
            destination=self.flat.well(0),
            volume="5:uL",
            liquid=ProteinBuffer,
            chip_material="silicone",
            nozzle="standard",
        )

        mode_params = {
            "x_tempest_chip": {
                "material": "silicone",
                "nozzle": "standard",
                "model": "high_volume",
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
                "nozzle": "standard",
                "model": "high_volume",
            }
        }
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
