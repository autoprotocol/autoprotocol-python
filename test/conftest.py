# pragma pylint: disable=missing-docstring
import pytest
import responses
from autoprotocol.container import Container
from autoprotocol.container_type import ContainerType
from autoprotocol.protocol import Protocol


@pytest.fixture(scope="module", autouse=True)
def run_around_tests():
    print("Define mock")

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/res-sw96-hp",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["universal"],
                        "capabilities": [
                            "incubate",
                            "liquid_handle",
                            "cover",
                            "uncover",
                            "dispense-destination",
                            "dispense-source",
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
                        "vendor": "Axygen",
                        # NOTE: NEED TO BE ADDED TO CONTAINER TYPE SERVICE
                        "true_max_vol_ul": "280000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/96-flat",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["low_evaporation", "standard", "universal"],
                        "capabilities": [
                            # TODO: TO BE ADDED
                            "cover",
                            "spin",
                            "incubate",
                            "absorbance",
                            "fluorescence",
                            "luminescence",
                            "image_plate",
                            "maxiprep_source",
                            "stamp",
                            "echo_dest",
                            "magnetic_transfer_pcr",
                            "bluewash",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "3632",
                        "col_count": 12,
                        "cost_each": "8.03",
                        # TODO: TO BE ADDED
                        "cover_types": ["low_evaporation", "standard", "universal"],
                        "dead_volume_ul": "25.0",
                        "height_mm": "14.22",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "96-Well White with Clear Flat Bottom Polystyrene Not Treated Microplate",
                        # NOTE: TO BE ADDED
                        "prioritize_seal_or_cover": "seal",
                        "retired_at": None,
                        "safe_min_volume_ul": "65.0",
                        "sale_price": "9.5557",
                        # NOTE: TO BE ADDED
                        "seal_types": [],
                        "shortname": "96-flat",
                        "well_count": 96,
                        "well_depth_mm": "10.67",
                        "well_volume_ul": "340.0",
                        "vendor": "Corning",
                        # NOTE: NEED TO BE ADDED TO CONTAINER TYPE SERVICE
                        "true_max_vol_ul": "340.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/96-pcr",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": [
                            "ultra-clear",
                            "foil",
                            "breathable",
                            "low_evaporation",
                        ],
                        "capabilities": [
                            "magnetic_separate",
                            "thermocycle",
                            "qrt_thermocycle",
                            "spin",
                            "incubate",
                            "seal",
                            "image_plate",
                            "sanger_sequence",
                            "miniprep_destination",
                            "stamp",
                            "flash_freeze",
                            "echo_dest",
                            "magnetic_transfer_pcr",
                            "bluewash",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "951020619",
                        "col_count": 12,
                        "cost_each": "4.14",
                        "dead_volume_ul": "3.0",
                        "height_mm": "15.9",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "96-Well twin.tec PCR Plate",
                        # NOTE: TO BE ADDED
                        "prioritize_seal_or_cover": "seal",
                        "retired_at": None,
                        "safe_min_volume_ul": "5.0",
                        "sale_price": "4.9266",
                        # NOTE: TO BE ADDED
                        "seal_types": ["ultra-clear", "foil"],
                        "shortname": "96-pcr",
                        # NOTE: NEED TO BE ADDED TO CONTAINER TYPE SERVICE
                        "true_max_vol_ul": "135.0",
                        "well_count": 96,
                        "well_depth_mm": "14.6",
                        "well_volume_ul": "160.0",
                        "vendor": "Eppendorf",
                    }
                }
            },
            status=200,
        )
        # TODO: NEED TO BE ADDED TO THE CONTAINER TYPES SERVICE
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/micro-1.5",
            json={
                "data": {
                    "attributes": {
                        "capabilities": [
                            "liquid_handle",
                            "gel_separate",
                            "gel_purify",
                            "incubate",
                            "spin",
                        ],
                        "col_count": 1,
                        "cost_each": "4.14",
                        "dead_volume_ul": "20.0",
                        "is_tube": True,
                        "manual_execution": False,
                        "name": "1.5mL Microcentrifuge tube",
                        "retired_at": None,
                        "safe_min_volume_ul": "20.0",
                        "shortname": "micro-1.5",
                        "sterile": False,
                        "well_count": 1,
                        "well_depth_mm": None,
                        "well_volume_ul": "1500.0",
                        "vendor": "USA Scientific",
                    }
                }
            },
            status=200,
        )
        # TODO: NEED TO BE ADDED TO THE CONTAINER TYPES SERVICE
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/micro-2.0",
            json={
                "data": {
                    "attributes": {
                        "name": "2mL Microcentrifuge tube",
                        "well_count": 1,
                        "well_depth_mm": None,
                        "well_volume_ul": "2000.0",
                        "well_coating": None,
                        "sterile": False,
                        "cover_types": None,
                        "seal_types": None,
                        "capabilities": [
                            "liquid_handle",
                            "gel_separate",
                            "gel_purify",
                            "incubate",
                            "spin",
                        ],
                        "shortname": "micro-2.0",
                        "is_tube": True,
                        "col_count": 1,
                        "dead_volume_ul": "5",
                        "safe_min_volume_ul": "40",
                        "vendor": "E&K Scientific",
                        "cat_no": "280200",
                        # TODO: TO BE ADDED
                        "true_max_vol_ul": "2000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/384-echo",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["universal", "foil", "ultra-clear"],
                        "capabilities": [
                            "spin",
                            "incubate",
                            "seal",
                            "image_plate",
                            "stamp",
                            "echo_dest",
                            "echo_source",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "PP-0200",
                        "col_count": 24,
                        "cost_each": "6.18",
                        "dead_volume_ul": "15.0",
                        "height_mm": "14.4",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "384-Well Echo Qualified Polypropylene Microplate 2.0",
                        "retired_at": None,
                        "safe_min_volume_ul": "15.0",
                        "sale_price": "7.3542",
                        "shortname": "384-echo",
                        # NOTE: NEED TO BE ADDED TO CONTAINER TYPE SERVICE
                        "true_max_vol_ul": "135.0",
                        "well_count": 384,
                        "well_depth_mm": "11.5",
                        "well_volume_ul": "135.0",
                        "vendor": "Labcyte",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/384-pcr",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["ultra-clear", "foil"],
                        "capabilities": [
                            "thermocycle",
                            "spin",
                            "incubate",
                            "qrt_thermocycle",
                            "seal",
                            "image_plate",
                            "stamp",
                            "flash_freeze",
                            "echo_dest",
                            "bluewash",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "951020539",
                        "col_count": 24,
                        "cost_each": "7.86",
                        "dead_volume_ul": "2.0",
                        "height_mm": "10.6",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "384-Well twin.tec PCR Plate",
                        "retired_at": None,
                        "safe_min_volume_ul": "3.0",
                        "sale_price": "9.3534",
                        # NOTE: TO BE ADDED
                        "seal_types": ["ultra-clear", "foil"],
                        "shortname": "384-pcr",
                        "well_count": 384,
                        "well_depth_mm": "9.6",
                        "well_volume_ul": "40.0",
                        "vendor": "Eppendorf",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/96-flat-uv",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["low_evaporation", "standard", "universal"],
                        "capabilities": [
                            # NOTE: TO BE ADDED
                            "cover",
                            "spin",
                            "incubate",
                            "absorbance",
                            "fluorescence",
                            "luminescence",
                            "image_plate",
                            "stamp",
                            "magnetic_transfer_pcr",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "3635",
                        "col_count": 12,
                        "cost_each": "14.1",
                        "cover_types": ["low_evaporation", "standard", "universal"],
                        "dead_volume_ul": "25.0",
                        "height_mm": "14.22",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "96-Well Clear Flat Bottom UV-Transparent Microplate",
                        "retired_at": None,
                        "safe_min_volume_ul": "65.0",
                        "sale_price": "16.779",
                        "shortname": "96-flat-uv",
                        "well_count": 96,
                        "well_depth_mm": "10.67",
                        "well_volume_ul": "340.0",
                        "vendor": "Corning",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/1-flat",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["universal"],
                        "capabilities": [
                            # TODO: TO BE ADDED
                            "cover",
                            "incubate",
                            "image_plate",
                            "colonize",
                            "envision",
                        ],
                        "catalog_number": "267060",
                        "col_count": 1,
                        "cost_each": "4.71",
                        # TODO: TO BE ADDED
                        "cover_types": ["universal"],
                        "dead_volume_ul": "36000.0",
                        "height_mm": "17.3",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "1-Well Nunc Non-treated Flat Bottom Plate",
                        "retired_at": None,
                        "safe_min_volume_ul": "40000.0",
                        "sale_price": "5.6049",
                        "shortname": "1-flat",
                        "well_count": 1,
                        "well_depth_mm": "11.6",
                        "well_volume_ul": "90000.0",
                        "vendor": "Fisher",
                        # TODO: TO BE ADDED
                        "true_max_vol_ul": "90000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/6-flat-tc",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["standard", "universal"],
                        "capabilities": [
                            # NOTE: TO BE ADDED
                            "cover",
                            "incubate",
                            "colonize",
                            "image_plate",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "30720113",
                        "col_count": 3,
                        "cost_each": "4.05",
                        # NOTE: TO BE ADDED
                        "cover_types": ["standard", "universal"],
                        "dead_volume_ul": "400.0",
                        "height_mm": "19.0",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "6-Well TC Treated Sterile Plate",
                        "retired_at": None,
                        "safe_min_volume_ul": "600.0",
                        "sale_price": "4.8195",
                        "shortname": "6-flat-tc",
                        "well_count": 6,
                        "well_depth_mm": "16.5",
                        "well_volume_ul": "5000.0",
                        "vendor": "Eppendorf",
                        # TODO: TO BE ADDED
                        "true_max_vol_ul": "5000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/384-flat",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["standard", "universal"],
                        "capabilities": [
                            "cover",
                            "spin",
                            "incubate",
                            "absorbance",
                            "fluorescence",
                            "luminescence",
                            "image_plate",
                            "stamp",
                            "echo_dest",
                            "bluewash",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "3706",
                        "col_count": 24,
                        "cost_each": "11.54",
                        # TODO: TO BE ADDED
                        "cover_types": ["standard", "universal"],
                        "dead_volume_ul": "5.0",
                        "height_mm": "14.22",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "384-Well Clear Bottom White Polystyrene Microplate",
                        # TODO: TO BE ADDED
                        "prioritize_seal_or_cover": "cover",
                        "retired_at": None,
                        "safe_min_volume_ul": "15.0",
                        "sale_price": "13.7326",
                        # TODO: TO BE ADDED
                        "seal_types": ["ultra-clear", "foil"],
                        "shortname": "384-flat",
                        "well_count": 384,
                        "well_depth_mm": "11.43",
                        "well_volume_ul": "90.0",
                        "vendor": "Corning",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/96-v-kf",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["standard"],
                        "capabilities": [
                            "pipette",
                            "stamp",
                            "spin",
                            "cover",
                            "uncover",
                            "incubate",
                            "magnetic_transfer_deep",
                            "magnetic_transfer_pcr",
                            "image_plate",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "22-387-030",
                        "col_count": 12,
                        "cost_each": "5.3",
                        # TODO: TO BE ADDED
                        "cover_types": ["standard"],
                        "dead_volume_ul": "20.0",
                        "height_mm": "14.5",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "96-well KingFisher PCR microplate",
                        "retired_at": None,
                        "safe_min_volume_ul": "20.0",
                        "sale_price": "6.307",
                        "shortname": "96-v-kf",
                        "well_count": 96,
                        "well_depth_mm": "12.9",
                        "well_volume_ul": "200.0",
                        "vendor": "Fisher",
                        # TODO: TO BE ADDED BY DEFAULT PLEASE!
                        "true_max_vol_ul": "200.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/96-deep-kf",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["standard"],
                        "capabilities": [
                            "pipette",
                            "stamp",
                            "spin",
                            "cover",
                            "uncover",
                            "incubate",
                            "magnetic_transfer_deep",
                            "image_plate",
                            "seal",
                            "deseal",
                            "dispense-destination",
                        ],
                        "catalog_number": "22-387-031",
                        "col_count": 12,
                        "cost_each": "8.25",
                        # TODO: TO BE ADDED
                        "cover_types": ["standard"],
                        "dead_volume_ul": "50.0",
                        "height_mm": "44.0",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "96-Well KingFisher Deepwell Plate V-bottom Polypropylene",
                        "retired_at": None,
                        "safe_min_volume_ul": "50.0",
                        "sale_price": "9.8175",
                        "shortname": "96-deep-kf",
                        "well_count": 96,
                        "well_depth_mm": "42.3",
                        "well_volume_ul": "1000.0",
                        "vendor": "Fisher",
                        # TODO: TO BE ADDED BY DEFAULT PLEASE!
                        "true_max_vol_ul": "1000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/96-deep",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["standard", "universal", "breathable"],
                        "capabilities": [
                            # TODO: TO BE ADDED
                            "cover",
                            "magnetic_separate",
                            "incubate",
                            "seal",
                            "image_plate",
                            "miniprep_source",
                            "maxiprep_source",
                            "maxiprep_destination",
                            "stamp",
                            "spin",
                            "magnetic_transfer_deep",
                            "deseal",
                            "flash_freeze",
                            "dispense-destination",
                        ],
                        "catalog_number": "3961",
                        "col_count": 12,
                        "cost_each": "8.35",
                        # TODO: TO BE ADDED
                        "cover_types": ["standard", "universal"],
                        "dead_volume_ul": "15.0",
                        "height_mm": "43.8",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "96-Well Clear V-Bottom Polypropylene Deep Well Plate",
                        # TODO: TO BE ADDED
                        "prioritize_seal_or_cover": "cover",
                        "retired_at": None,
                        "safe_min_volume_ul": "30.0",
                        "sale_price": "9.9365",
                        # TODO: TO BE ADDED
                        "seal_types": ["breathable"],
                        "shortname": "96-deep",
                        "well_count": 96,
                        "well_depth_mm": "42.03",
                        "well_volume_ul": "2000.0",
                        "vendor": "Corning",
                        # TODO: TO BE ADDED BY DEFAULT PLEASE!
                        "true_max_vol_ul": "2000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/6-flat",
            json={
                "data": {
                    "attributes": {
                        "acceptable_lids": ["standard", "universal"],
                        "capabilities": [
                            "cover",
                            "incubate",
                            "colonize",
                            "image_plate",
                            "dispense-destination",
                            "envision",
                        ],
                        "catalog_number": "30720016",
                        "col_count": 3,
                        "cost_each": "3.78",
                        # TODO: TO BE ADDED
                        "cover_types": ["standard", "universal"],
                        "dead_volume_ul": "400.0",
                        "height_mm": "19.0",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "6-Well Non-Treated Sterile Plate",
                        "retired_at": None,
                        "safe_min_volume_ul": "600.0",
                        "sale_price": "4.4982",
                        "shortname": "6-flat",
                        "well_count": 6,
                        "well_depth_mm": "16.5",
                        "well_volume_ul": "5000.0",
                        "vendor": "Eppendorf",
                        # TODO: TO BE ADDED BY DEFAULT PLEASE!
                        "true_max_vol_ul": "5000.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/dummy",
            json={
                "data": {
                    "attributes": {
                        "capabilities": [],
                        "catalog_number": "30720016",
                        "col_count": 5,
                        "cover_types": [],
                        "dead_volume_ul": "400.0",
                        "height_mm": "19.0",
                        "is_tube": False,
                        "manual_execution": False,
                        "name": "Dummy",
                        "retired_at": None,
                        "safe_min_volume_ul": "600.0",
                        "sale_price": "4.4982",
                        "shortname": "dummy",
                        "well_count": 15,
                        "well_depth_mm": None,
                        "well_volume_ul": "200.0",
                        "true_max_vol_ul": "200.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/dummy-tube",
            json={
                "data": {
                    "attributes": {
                        "capabilities": [],
                        "catalog_number": "30720016",
                        "col_count": 5,
                        "cover_types": [],
                        "dead_volume_ul": "15.0",
                        "height_mm": "19.0",
                        "is_tube": True,
                        "manual_execution": False,
                        "name": "Dummy tube",
                        "retired_at": None,
                        "safe_min_volume_ul": "30.0",
                        "sale_price": "4.4982",
                        "shortname": "dummy-tube",
                        "well_count": 1,
                        "well_depth_mm": None,
                        "well_volume_ul": "200.0",
                        "vendor": "Eppendorf",
                        "true_max_vol_ul": "200.0",
                    }
                }
            },
            status=200,
        )
        rsps.add(
            rsps.GET,
            "https://secure.strateos.com/api/container_types/dummy-big",
            json={
                "data": {
                    "attributes": {
                        "capabilities": [],
                        "col_count": 5,
                        "cover_types": [],
                        "dead_volume_ul": "15.0",
                        "height_mm": "19.0",
                        "is_tube": True,
                        "manual_execution": False,
                        "name": "Dummy tube",
                        "retired_at": None,
                        "safe_min_volume_ul": "30.0",
                        "sale_price": "4.4982",
                        "shortname": "dummy-tube",
                        "well_count": 20,
                        "well_depth_mm": None,
                        "well_volume_ul": "200.0",
                        "vendor": "Eppendorf",
                        "true_max_vol_ul": "200.0",
                    }
                }
            },
            status=200,
        )
        yield


@pytest.fixture(scope="function")
def dummy_protocol():
    yield Protocol()


@pytest.fixture(scope="module")
def dummy_type():
    return ContainerType("dummy")


@pytest.fixture(scope="module")
def dummy_tube():
    return Container(None, ContainerType("dummy-tube"),)


@pytest.fixture(scope="module")
def dummy_big():
    return Container(None, ContainerType("dummy-big"),)


@pytest.fixture(scope="module")
def dummy_96():
    return Container(None, ContainerType("96-flat"),)


@pytest.fixture(scope="module")
def dummy_reservoir_row():
    container_type = ContainerType("dummy")
    container_type.well_count = 8
    container_type.col_count = 1
    return Container(None, container_type,)


@pytest.fixture(scope="module")
def dummy_reservoir_column():
    container_type = ContainerType("dummy")
    container_type.well_count = 12
    container_type.col_count = 12
    return Container(None, container_type,)


@pytest.fixture(scope="module")
def dummy_24():
    container_type = ContainerType("dummy")
    container_type.well_count = 24
    container_type.col_count = 6
    return Container(None, container_type,)


@pytest.fixture(scope="module")
def dummy_384():
    return Container(None, ContainerType("384-echo"))


@pytest.fixture(scope="module")
def dummy_1536():
    container_type = ContainerType("dummy")
    container_type.well_count = 1536
    container_type.col_count = 48
    return Container(None, container_type,)


@pytest.fixture(scope="module")
def dummy_pathological():
    container_type = ContainerType("dummy")
    container_type.well_count = 384
    container_type.col_count = 96
    return Container(None, container_type,)
