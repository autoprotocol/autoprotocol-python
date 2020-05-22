# pragma pylint: disable=missing-docstring
import pytest
from autoprotocol.container import Container
from autoprotocol.container_type import ContainerType
from autoprotocol.unit import Unit
from autoprotocol.protocol import Protocol


@pytest.fixture(scope="function")
def dummy_protocol():
    yield Protocol()


@pytest.fixture(scope="module")
def dummy_type():
    return ContainerType(
        name="dummy",
        well_count=15,
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
