import json
from test.test_util import TestUtils
import pytest

from autoprotocol.protocol import Protocol

class TestProvision(object):
    p = Protocol()
    w1 = p.ref("w1", None, cont_type="96-pcr", discard=True) \
        .well(0).set_volume("2:microliter")

    def test_provision_well_capacity(self):
        self.p.provision("rs17gmh5wafm5p", self.w1, "50:microliter")
        actual_protocol_as_json = json.dumps(self.p.as_dict()['instructions'], indent=2, sort_keys=True)
        expected_protocol_as_json = TestUtils.read_json_file('expected_provision.json')

        assert (expected_protocol_as_json == actual_protocol_as_json)

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
        p = Protocol()
        w1 = p.ref("w1", None, cont_type="96-pcr", discard=True) \
            .well(0).set_volume("2:microliter")
        w2 = p.ref("w2", None, cont_type="96-pcr", discard=True) \
            .well(0).set_volume("2:microliter")
        w3 = p.ref("w3", None, cont_type="96-pcr", discard=True) \
            .well(0).set_volume("2:microliter")
        wells = [w1, w2, w3]
        p.provision("rs17gmh5wafm5p", wells, "50:microliter")
        actual_protocol_as_json = json.dumps(p.as_dict()['instructions'], indent=2, sort_keys=True)
        expected_protocol_as_json = TestUtils.read_json_file('provision_multiple_wells.json')

        assert (expected_protocol_as_json == actual_protocol_as_json)

    def test_with_multiple_wells_with_different_cont_types(self):
        p = Protocol()
        w1 = p.ref("w1", None, cont_type="1-flat", discard=True) \
            .well(0).set_volume("2:microliter")
        w2 = p.ref("w2", None, cont_type="6-flat-tc", discard=True) \
            .well(0).set_volume("2:microliter")
        wells = [w1, w2]
        p.provision("rs17gmh5wafm5p", wells, "1500:microliter")
        actual_protocol_as_json = json.dumps(p.as_dict()['instructions'], indent=2, sort_keys=True)
        expected_protocol_as_json = TestUtils.read_json_file('provision_multiple_wells_with_diff_cont_types.json')

        assert (expected_protocol_as_json == actual_protocol_as_json)

    def test_provision_with_covered_container(self):
        p = Protocol()
        w1 = p.ref("w1", None, cont_type="96-pcr", discard=True, cover="standard") \
            .well(0).set_volume("2:microliter")
        p.provision("rs17gmh5wafm5p", w1, "50:microliter")
        actual_protocol_as_json = json.dumps(p.as_dict()['instructions'], indent=2, sort_keys=True)
        expected_protocol_as_json = TestUtils.read_json_file('provision_with_cover.json')

        assert (expected_protocol_as_json == actual_protocol_as_json)

    def test_provision_with_sealed_container(self):
        p = Protocol()
        w1 = p.ref("w1", None, cont_type="96-pcr", discard=True, cover="foil") \
            .well(0).set_volume("2:microliter")
        p.provision("rs17gmh5wafm5p", w1, "50:microliter")
        actual_protocol_as_json = json.dumps(p.as_dict()['instructions'], indent=2, sort_keys=True)
        expected_protocol_as_json = TestUtils.read_json_file('provision_with_seal.json')

        assert (expected_protocol_as_json == actual_protocol_as_json)

    def test_for_multiple_dispenses_of_resource_in_containers_larger_than_900ml(self):
        p = Protocol()
        w1 = p.ref("w1", None, cont_type="micro-2.0", discard=True) \
            .well(0).set_volume("2:microliter")
        p.provision("rs17gmh5wafm5p", w1, "1500:microliter")

        actual_protocol_as_json = json.dumps(p.as_dict()['instructions'], indent=2, sort_keys=True)
        expected_protocol_as_json = TestUtils.read_json_file('split_provisions_by_volume.json')
        assert (expected_protocol_as_json == actual_protocol_as_json)
