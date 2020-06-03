import json
from test.test_util import TestUtils
import pytest

from autoprotocol.protocol import Protocol


class TestProvision(object):
    @pytest.fixture(autouse=True)
    def setup(self):
        # pylint: disable=attribute-defined-outside-init
        self.p = Protocol()
        # pylint: disable=attribute-defined-outside-init
        self.w1 = (
            self.p.ref("w1", None, cont_type="96-pcr", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )

    def test_provision_well_capacity(self):
        self.p.provision("rs17gmh5wafm5p", self.w1, "50:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "expected_provision.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_attempt_to_provision_more_than_well_capacity(self):
        with pytest.raises(ValueError):
            self.p.provision("rs17gmh5wafm5p", self.w1, "500:microliter")

    def test_with_invalid_resource_id(self):
        with pytest.raises(TypeError):
            self.p.provision(100, self.w1, "50:microliter")

    def test_with_destinations_count_not_same_as_volumes(self):
        volumes = ["50:microliter", "20:microliter"]
        with pytest.raises(RuntimeError):
            self.p.provision("rs17gmh5wafm5p", self.w1, volumes)

    def test_with_volume_above_max(self):
        with pytest.raises(ValueError):
            self.p.provision("rs17gmh5wafm5p", self.w1, "200:microliter")

    def test_with_multiple_wells(self):
        w2 = (
            self.p.ref("w2", None, cont_type="96-pcr", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        w3 = (
            self.p.ref("w3", None, cont_type="96-pcr", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        wells = [self.w1, w2, w3]
        self.p.provision("rs17gmh5wafm5p", wells, "50:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_multiple_wells.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_with_consecutive_repeated_wells(self):
        wells = [self.w1, self.w1]
        self.p.provision("rs17gmh5wafm5p", wells, "50:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_with_consecutive_repeated_wells.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_with_repeated_wells_but_discontinuous(self):
        w2 = (
            self.p.ref("w2", None, cont_type="96-pcr", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        wells = [self.w1, w2, self.w1]
        self.p.provision("rs17gmh5wafm5p", wells, "50:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_with_repeated_wells_but_discontinuous.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_with_multiple_wells_with_different_cont_types(self):
        self.p.refs.clear()
        w1 = (
            self.p.ref("w1", None, cont_type="1-flat", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        w2 = (
            self.p.ref("w2", None, cont_type="6-flat-tc", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        wells = [w1, w2]
        self.p.provision("rs17gmh5wafm5p", wells, "1500:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_multiple_wells_with_diff_cont_types.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_provision_with_covered_container(self):
        self.p.refs.clear()
        w1 = (
            self.p.ref("w1", None, cont_type="96-pcr", discard=True, cover="standard")
            .well(0)
            .set_volume("2:microliter")
        )
        self.p.provision("rs17gmh5wafm5p", w1, "50:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_with_cover.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_provision_with_sealed_container(self):
        self.p.refs.clear()
        w1 = (
            self.p.ref("w1", None, cont_type="96-pcr", discard=True, cover="foil")
            .well(0)
            .set_volume("2:microliter")
        )
        self.p.provision("rs17gmh5wafm5p", w1, "50:microliter")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_with_seal.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_for_multiple_dispenses_of_resource_in_containers_larger_than_900ml(self):
        self.p.refs.clear()
        w1 = (
            self.p.ref("w1", None, cont_type="micro-2.0", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        self.p.provision("rs17gmh5wafm5p", w1, volumes="1500:microliter")

        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "split_provisions_by_volume.json"
        )
        assert expected_instruction_as_json == actual_instruction_as_json

    def test_provision_well_with_mass(self):
        self.p.provision("rs17gmh5wafm5p", self.w1, amounts="50:ug")
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_for_mass.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_provision_multiple_wells_with_diff_masses(self):
        w2 = (
            self.p.ref("w2", None, cont_type="96-pcr", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        self.p.provision("rs17gmh5wafm5p", [self.w1, w2], ["50:ug", "25:mg"])
        actual_instruction_as_json = json.dumps(
            self.p.as_dict()["instructions"], indent=2, sort_keys=True
        )
        expected_instruction_as_json = TestUtils.read_json_file(
            "provision_with_more_than_one_mass.json"
        )

        assert expected_instruction_as_json == actual_instruction_as_json

    def test_provision_wells_with_amounts_of_varying_measurement_modes(self):
        w2 = (
            self.p.ref("w2", None, cont_type="96-pcr", discard=True)
            .well(0)
            .set_volume("2:microliter")
        )
        with pytest.raises(ValueError):
            self.p.provision("rs17gmh5wafm5p", [self.w1, w2], ["50:lb", "50:gallon"])

    def test_provision_passing_both_volumes_and_amounts(self):
        with pytest.raises(ValueError):
            self.p.provision("rs17gmh5wafm5p", self.w1, "25:ul", "50:mg")

    def test_provision_well_with_neither_mass_nor_volume(self):
        with pytest.raises(ValueError):
            self.p.provision("rs17gmh5wafm5p", self.w1)
