import pytest
import responses

from autoprotocol import Unit


# class TestContainerRobotize(object):
    # def test_robotize_decompose(self, dummy_type):
    #     for ref in ["a1", "A1", "0", 0]:
    #         assert 0 == dummy_type.robotize(ref)
    #         assert (0, 0) == dummy_type.decompose(ref)

    #     for ref in ["a5", "A5", "4", 4]:
    #         assert 4 == dummy_type.robotize(ref)
    #         assert (0, 4) == dummy_type.decompose(ref)

    #     for ref in ["b1", "B1", "5", 5]:
    #         assert 5 == dummy_type.robotize(ref)
    #         assert (1, 0) == dummy_type.decompose(ref)

    #     for ref in ["c5", "C5", "14", 14]:
    #         assert 14 == dummy_type.robotize(ref)
    #         assert (2, 4) == dummy_type.decompose(ref)

    #     assert [0, 5] == dummy_type.robotize(["A1", "B1"])

#     def test_robotize_1536(self, dummy_1536):
#         assert [1535, 516, 0] == dummy_1536.robotize(["Af48", "k37", "a1"])
#         for ref in [1.0, 2.3]:
#             with pytest.raises(TypeError):
#                 dummy_1536.robotize(ref)
#         for ref in [-1, "abc", "2a2"]:
#             with pytest.raises(ValueError):
#                 dummy_1536.robotize(ref)

#     def test_humanize_1536(self, dummy_1536):
#         assert ["AF48", "K37", "A1"] == dummy_1536.humanize([1535, 516, 0])
#         for ref in [1.0, 2.3, "abc", "2a2"]:
#             with pytest.raises(TypeError):
#                 dummy_1536.humanize(ref)
#         for ref in [-1, 1536]:
#             with pytest.raises(ValueError):
#                 dummy_1536.humanize(ref)

#     def test_robotize_decompose_checks(self, dummy_type):
#         for ref in [1.0, 4.3]:
#             with pytest.raises(TypeError):
#                 dummy_type.robotize(ref)
#             with pytest.raises(TypeError):
#                 dummy_type.decompose(ref)

#         for ref in [["A1", "B1"]]:
#             with pytest.raises(TypeError):
#                 dummy_type.decompose(ref)

#         for ref in ["D1", "A6", 15, "2A2"]:
#             with pytest.raises(ValueError):
#                 dummy_type.robotize(ref)
#             with pytest.raises(ValueError):
#                 dummy_type.decompose(ref)

#     def test_humanize(self, dummy_type):
#         assert "A1" == dummy_type.humanize(0)
#         assert "A5" == dummy_type.humanize(4)
#         assert "B2" == dummy_type.humanize(6)
#         assert "C5" == dummy_type.humanize(14)
#         assert ["A1", "B2"] == dummy_type.humanize([0, 6])
#         assert ["A1", "B2"] == dummy_type.humanize(["0", "6"])

#         with pytest.raises(TypeError):
#             dummy_type.humanize("0.1")
#         with pytest.raises(ValueError):
#             dummy_type.humanize(15)
#         with pytest.raises(TypeError):
#             dummy_type.humanize("A1")


# class TestAllContainerTypes(object):
#     def test_all_container_types(self):
#         from autoprotocol.container_type import _CONTAINER_TYPES
#         from autoprotocol.protocol import Protocol

#         p = Protocol()

#         for k, v in _CONTAINER_TYPES.items():
#             p.ref(k, None, v.shortname, discard=True)

#         assert len(p.refs) == len(_CONTAINER_TYPES)


# class TestContainerTypeVolumes(object):
#     def test_true_vol_default(self, dummy_type):
#         assert dummy_type.true_max_vol_ul == dummy_type.well_volume_ul


# class TestContainerTypeAttributes(object):
#     def test_default_attributes(self, dummy_type):
#         assert dummy_type.vendor is None
#         assert dummy_type.cat_no is None
#         assert dummy_type.true_max_vol_ul == dummy_type.well_volume_ul

#     def test_echo_attributes(self, dummy_echo):
#         assert dummy_echo.container_type.vendor == "Labcyte"
#         assert dummy_echo.container_type.cat_no is None
#         assert (
#             dummy_echo.container_type.true_max_vol_ul
#             > dummy_echo.container_type.well_volume_ul
#         )

class TestContainerType(object):
    def test_instance(self):
        from autoprotocol.container_type import ContainerType

        responses.add(
            responses.GET,
            'https://secure.strateos.com/api/container_types/res-sw96-hp',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": ["universal"],
                        "capabilities": [
                            "incubate",
                            "liquid_handle",
                            "cover",
                            "uncover",
                            "dispense-destination",
                            "dispense-source"
                        ],
                        "catalog_number": "res-sw96-hp",
                        "col_count": 1,
                        "cost_each": "7.02",
                        "dead_volume_ul": None,
                        "height_mm": "43.92",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "1-Well Reagent Reservoir with 96-Bottom Troughs, High Profile",
                        "retired_at": None,
                        "safe_min_volume_ul": None,
                        "sale_price": "8.3538",
                        "shortname": "res-sw96-hp",
                        "well_count": 1,
                        "well_depth_mm": "38.6",
                        "well_volume_ul": "280000.0",
                        "vendor": "Axygen"

                    }
                }
            },
            status=200
        )

        ct = ContainerType("res-sw96-hp")

        assert ct.shortname == "res-sw96-hp"
        assert len(responses.calls) == 1
        assert ct.well_count == 1
        assert ct.col_count == 1
        assert ct.acceptable_lids == ["universal"]
        assert ct.well_volume_ul == Unit(280000.0, "microliter")
        assert ct.is_tube == False
        assert ct.height_mm == 43.92
        assert ct.well_depth_mm == 38.6
        assert ct.dead_volume_ul == None
