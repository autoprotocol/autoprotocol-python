# pragma pylint: disable=missing-docstring
import pytest
import responses
from autoprotocol.container import Container
from autoprotocol.container_type import ContainerType
from autoprotocol.protocol import Protocol
from test.test_util import TestUtils


@pytest.fixture(scope="module", autouse=True)
def mock_requests():
    print("Define mock")

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        requests = TestUtils.load_json_file("container_types.json")

        for request in requests:
            rsps.add(
                rsps.GET,
                request["url"],
                json=request["body"],
                status=200,
            )
        yield rsps

    print("**** teardown")


@pytest.fixture(scope="function")
def dummy_protocol():
    yield Protocol()


@pytest.fixture(scope="module")
def dummy_type():
    return ContainerType("dummy")


@pytest.fixture(scope="module")
def dummy_tube():
    return Container(
        None,
        ContainerType("dummy-tube"),
    )


@pytest.fixture(scope="module")
def dummy_big():
    return Container(
        None,
        ContainerType("dummy-big"),
    )


@pytest.fixture(scope="module")
def dummy_96():
    return Container(
        None,
        ContainerType("96-flat"),
    )


@pytest.fixture(scope="module")
def dummy_reservoir_row():
    container_type = ContainerType("dummy")
    container_type.well_count = 8
    container_type.col_count = 1
    return Container(
        None,
        container_type,
    )


@pytest.fixture(scope="module")
def dummy_reservoir_column():
    container_type = ContainerType("dummy")
    container_type.well_count = 12
    container_type.col_count = 12
    return Container(
        None,
        container_type,
    )


@pytest.fixture(scope="module")
def dummy_24():
    container_type = ContainerType("dummy")
    container_type.well_count = 24
    container_type.col_count = 6
    return Container(
        None,
        container_type,
    )


@pytest.fixture(scope="module")
def dummy_384():
    return Container(None, ContainerType("384-echo"))


@pytest.fixture(scope="module")
def dummy_1536():
    container_type = ContainerType("dummy")
    container_type.well_count = 1536
    container_type.col_count = 48
    return Container(
        None,
        container_type,
    )


@pytest.fixture(scope="module")
def dummy_pathological():
    container_type = ContainerType("dummy")
    container_type.well_count = 384
    container_type.col_count = 96
    return Container(
        None,
        container_type,
    )
