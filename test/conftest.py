# pragma pylint: disable=missing-docstring
import pytest
import responses
from autoprotocol.container import Container
from autoprotocol.container_type import ContainerType
from autoprotocol.unit import Unit
from autoprotocol.protocol import Protocol

@pytest.fixture(scope="module", autouse=True)
def run_around_tests():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            rsps.GET,
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
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/96-flat',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "low_evaporation",
                            "standard",
                            "universal"
                        ],
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
                            "envision"
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
                        "vendor": "Corning"
                    }
                }
            },
            status=200
        )
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/96-pcr',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "ultra-clear",
                            "foil",
                            "breathable",
                            "low_evaporation"
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
                            "envision"
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
                        "vendor": "Eppendorf"
                    }
                }
            },
            status=200
        )
        # TODO: NEED TO BE ADDED TO THE CONTAINER TYPES SERVICE
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/micro-1.5',
            json={
                'data': {
                    'attributes': {
                        "capabilities": [
                            "liquid_handle",
                            "gel_separate",
                            "gel_purify",
                            "incubate",
                            "spin"
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
                        "vendor": "USA Scientific"
                    }
                }
            },
            status=200
        )
        # TODO: NEED TO BE ADDED TO THE CONTAINER TYPES SERVICE
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/micro-2.0',
            json={
                'data': {
                    'attributes': {
                        "name": "2mL Microcentrifuge tube",
                        "well_count": 1,
                        "well_depth_mm": None,
                        "well_volume_ul": "2000.0",
                        "well_coating": None,
                        "sterile": False,
                        "cover_types": None,
                        "seal_types": None,
                        "capabilities": ["liquid_handle", "gel_separate", "gel_purify", "incubate", "spin"],
                        "shortname": "micro-2.0",
                        "is_tube": True,
                        "col_count": 1,
                        "dead_volume_ul": "5",
                        "safe_min_volume_ul": "40",
                        "vendor": "E&K Scientific",
                        "cat_no": "280200",
                        # TODO: TO BE ADDED
                        "true_max_vol_ul": "2000.0"
                    }
                }
            },
            status=200
        )
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/384-echo',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "universal",
                            "foil",
                            "ultra-clear"
                        ],
                        "capabilities": [
                            "spin",
                            "incubate",
                            "seal",
                            "image_plate",
                            "stamp",
                            "echo_dest",
                            "echo_source",
                            "dispense-destination",
                            "envision"
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
                        "vendor": "Labcyte"
                    }
                }
            },
            status=200
        )
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/384-pcr',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "ultra-clear",
                            "foil"
                        ],
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
                            "envision"
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
                        "vendor": "Eppendorf"
                    }
                }
            },
            status=200
        )
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/96-flat-uv',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "low_evaporation",
                            "standard",
                            "universal"
                        ],
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
                            "envision"
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
                        "vendor": "Corning"
                    }
                }
            },
            status=200
        )
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/1-flat',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "universal"
                        ],
                        "capabilities": [
                            # TODO: TO BE ADDED
                            "cover",
                            "incubate",
                            "image_plate",
                            "colonize",
                            "envision"
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
                        "true_max_vol_ul": "90000.0"
                    }
                }
            },
            status=200
        )
        rsps.add(
            rsps.GET,
            'https://secure.strateos.com/api/container_types/6-flat-tc',
            json={
                'data': {
                    'attributes': {
                        "acceptable_lids": [
                            "standard",
                            "universal"
                        ],
                        "capabilities": [
                            # NOTE: TO BE ADDED
                            "cover",
                            "incubate",
                            "colonize",
                            "image_plate",
                            "dispense-destination",
                            "envision"
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
                        "true_max_vol_ul": "5000.0"
                    }
                }
            },
            status=200
        )
        yield


@pytest.fixture(scope="function")
def dummy_protocol():
    yield Protocol()


@pytest.fixture(scope="module")
def dummy_type():
    return ContainerType(
        # name="dummy",
        # well_count=15,
        # well_depth_mm=None,
        # well_volume_ul=Unit(200, "microliter"),
        # well_coating=None,
        # sterile=False,
        # is_tube=False,
        # cover_types=[],
        # seal_types=None,
        # capabilities=[],
        shortname="dummy" #,
        # col_count=5,
        # dead_volume_ul=Unit(15, "microliter"),
        # safe_min_volume_ul=Unit(30, "microliter"),
    )


@pytest.fixture(scope="module")
def dummy_tube():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=1,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=True,
            cover_types=[],
            seal_types=None,
            capabilities=[],
            shortname="dummy",
            col_count=1,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_big():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=20,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=[],
            seal_types=None,
            capabilities=[],
            shortname="dummy",
            col_count=5,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_96():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=96,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=["universal"],
            seal_types=None,
            capabilities=["cover"],
            shortname="dummy",
            col_count=12,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_reservoir_row():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=8,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=None,
            seal_types=None,
            capabilities=None,
            shortname="dummy",
            col_count=1,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_reservoir_column():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=12,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=None,
            seal_types=None,
            capabilities=None,
            shortname="dummy",
            col_count=12,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_24():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=24,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=None,
            seal_types=None,
            capabilities=None,
            shortname="dummy",
            col_count=6,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_384():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=384,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=[],
            seal_types=None,
            capabilities=[],
            shortname="dummy",
            col_count=24,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_1536():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=1536,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=[],
            seal_types=None,
            capabilities=[],
            shortname="dummy",
            col_count=48,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_pathological():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=384,
            well_depth_mm=None,
            well_volume_ul=Unit(200, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=[],
            seal_types=None,
            capabilities=[],
            shortname="dummy",
            col_count=96,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(30, "microliter"),
        ),
    )


@pytest.fixture(scope="module")
def dummy_echo():
    return Container(
        None,
        ContainerType(
            name="dummy",
            well_count=384,
            well_depth_mm=None,
            well_volume_ul=Unit(65, "microliter"),
            well_coating=None,
            sterile=False,
            is_tube=False,
            cover_types=[],
            seal_types=None,
            capabilities=[],
            shortname="dummy",
            col_count=96,
            dead_volume_ul=Unit(15, "microliter"),
            safe_min_volume_ul=Unit(15, "microliter"),
            true_max_vol_ul=Unit(135, "microliter"),
            vendor="Labcyte",
        ),
    )
