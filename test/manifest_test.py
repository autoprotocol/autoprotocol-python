import pytest
from autoprotocol.harness import (
    ProtocolInfo,
    Manifest,
    seal_on_store,
    get_protocol_preview,
)
from autoprotocol import Protocol, Unit, Well, WellGroup
import json


class TestManifest(object):
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.protocol = Protocol()

    def test_empty(self):
        protocol_info = ProtocolInfo({"name": "Test Empty", "inputs": {}})
        parsed = protocol_info.parse(self.protocol, {"refs": {}, "parameters": {}})
        assert {} == parsed

    def test_basic_types(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Types",
                "inputs": {
                    "bool": "bool",
                    "string": "string",
                    "integer": "integer",
                    "decimal": "decimal",
                },
            }
        )
        parsed = protocol_info.parse(
            self.protocol,
            {
                "refs": {},
                "parameters": {
                    "bool": True,
                    "string": "test",
                    "integer": 3,
                    "decimal": 2.1,
                },
            },
        )
        assert {"bool": True, "string": "test", "integer": 3, "decimal": 2.1} == parsed
        with pytest.raises(RuntimeError):
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {},
                    "parameters": {
                        "bool": True,
                        "string": "test",
                        "integer": "hi",
                        "decimal": 2.1,
                    },
                },
            )
        with pytest.raises(RuntimeError):
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {},
                    "parameters": {
                        "bool": True,
                        "string": "test",
                        "integer": "3",
                        "decimal": "hi",
                    },
                },
            )

    def test_unit_types(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Types",
                "inputs": {
                    "volume": "volume",
                    "time": "time",
                    "temperature": "temperature",
                },
            }
        )
        parsed = protocol_info.parse(
            self.protocol,
            {
                "refs": {},
                "parameters": {
                    "volume": "3:microliter",
                    "time": "30:second",
                    "temperature": "25:celsius",
                },
            },
        )
        assert {
            "volume": Unit.fromstring("3:microliter"),
            "time": Unit.fromstring("30:second"),
            "temperature": Unit.fromstring("25:celsius"),
        } == parsed
        with pytest.raises(RuntimeError):
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {},
                    "parameters": {
                        "volume": 3,
                        "time": "30:second",
                        "temperature": "25:celsius",
                    },
                },
            )
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {},
                    "parameters": {
                        "volume": "3:microliter",
                        "time": "hello",
                        "temperature": "25:celsius",
                    },
                },
            )
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {},
                    "parameters": {
                        "volume": "3:microliter",
                        "time": "30:second",
                        "temperature": 25,
                    },
                },
            )

    def test_group(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Types",
                "inputs": {
                    "group_test": {"type": "group", "inputs": {"test": "aliquot"}}
                },
            }
        )
        parsed = protocol_info.parse(
            self.protocol,
            {
                "refs": {
                    "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                },
                "parameters": {"group_test": {"test": "ct1test/0"}},
            },
        )
        assert isinstance(parsed["group_test"], dict)
        assert "test" in parsed["group_test"]
        assert isinstance(parsed["group_test"]["test"], Well)
        with pytest.raises(RuntimeError):
            protocol_info1 = ProtocolInfo(
                {
                    "name": "Test Errors",
                    "inputs": {
                        "group": {
                            "type": "group",
                            "inputs": {
                                "bool": "bool",
                                "aliquot": "aliquot",
                                "aliquot+": "aliquot+",
                            },
                        }
                    },
                }
            )
            protocol_info1.parse(
                self.protocol, {"refs": {}, "parameters": {"group": ["hello"]}}
            )
        with pytest.raises(RuntimeError):
            protocol_info2 = ProtocolInfo(
                {"name": "Test Errors", "inputs": {"group": {"type": "group"}}}
            )
            protocol_info2.parse(
                self.protocol,
                {
                    "refs": {},
                    "parameters": {
                        "group": {
                            "bool": True,
                            "aliquot": "dummy/0",
                            "aliquot+": ["dummy/0"],
                        }
                    },
                },
            )

    def test_multigroup(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Types",
                "inputs": {
                    "group_test": {"type": "group+", "inputs": {"test": "aliquot"}}
                },
            }
        )
        parsed = protocol_info.parse(
            self.protocol,
            {
                "refs": {
                    "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                },
                "parameters": {
                    "group_test": [{"test": "ct1test/0"}, {"test": "ct1test/1"}]
                },
            },
        )
        assert isinstance(parsed["group_test"], list)
        assert 2 == len(parsed["group_test"])
        assert "test" in parsed["group_test"][0]
        assert isinstance(parsed["group_test"][0]["test"], Well)
        assert "test" in parsed["group_test"][1]
        assert isinstance(parsed["group_test"][1]["test"], Well)
        assert 1 == parsed["group_test"][1]["test"].index

        # pragma pylint: disable=duplicate-key
        with pytest.raises(RuntimeError):
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {
                        "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                    },
                    "parameters": {
                        "group_test": {"test": "ct1test/0", "test": "ct1test/1"}
                    },
                },
            )
            protocol_info = ProtocolInfo(
                {
                    "name": "Test Basic Types",
                    "inputs": {"group_test": {"type": "group+"}},
                }
            )
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {
                        "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                    },
                    "parameters": {
                        "group_test": [{"test": "ct1test/0"}, {"test": "ct1test/1"}]
                    },
                },
            )
        # pragma pylint: enable=duplicate-key

    def test_group_choice(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Types",
                "inputs": {
                    "group_test": {
                        "type": "group-choice",
                        "options": [
                            {"value": "a", "inputs": {"test": "aliquot"}},
                            {"value": "b"},
                        ],
                    }
                },
            }
        )
        parsed = protocol_info.parse(
            self.protocol,
            {
                "refs": {
                    "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                },
                "parameters": {
                    "group_test": {
                        "value": "a",
                        "inputs": {"a": {"test": "ct1test/0"}, "b": {}},
                    }
                },
            },
        )
        assert isinstance(parsed["group_test"], dict)
        assert "a" == parsed["group_test"]["value"]
        assert "a" in parsed["group_test"]["inputs"]
        assert "b" not in parsed["group_test"]["inputs"]
        assert isinstance(parsed["group_test"]["inputs"]["a"]["test"], Well)
        with pytest.raises(RuntimeError):
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {
                        "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                    },
                    "parameters": {"group_test": {"value": "a"}},
                },
            )
            parsed = protocol_info.parse(
                self.protocol,
                {
                    "refs": {
                        "ct1test": {"id": "ct1test", "type": "96-pcr", "discard": True}
                    },
                    "parameters": {
                        "group_test": {"inputs": {"a": {"test": "ct1test/0"}, "b": {}}}
                    },
                },
            )

    def test_csv_table(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Types",
                "inputs": {
                    "table_test": {
                        "template": {
                            "header": [
                                "Destination Well",
                                "Source Well",
                                "Final concentration in ug/ml",
                            ],
                            "keys": [
                                "dest_well",
                                "source_well",
                                "final_concentration_ugml",
                            ],
                            "col_type": ["integer", "aliquot", "decimal"],
                            "rows": [
                                ["0", "ct17652537/0", "1.2"],
                                ["1", "ct17652537/0", "4.37"],
                            ],
                            "label": "Test Table CSV",
                        },
                        "type": "csv-table",
                        "label": "test table label",
                    }
                },
            }
        )
        parsed = protocol_info.parse(
            self.protocol,
            {
                "refs": {
                    "ct1test": {"id": "ct1test", "type": "micro-1.5", "discard": True},
                    "ct2test": {"id": "ct2test", "type": "micro-1.5", "discard": True},
                },
                "parameters": {
                    "table_test": [
                        {
                            "dest_well": "integer",
                            "source_well": "aliquot",
                            "final_concentration_ugml": "decimal",
                        },
                        [
                            {
                                "dest_well": 0,
                                "source_well": "ct1test/0",
                                "final_concentration_ugml": 0.5,
                            },
                            {
                                "dest_well": 1,
                                "source_well": "ct2test/0",
                                "final_concentration_ugml": 0.6,
                            },
                        ],
                    ]
                },
            },
        )
        assert isinstance(parsed["table_test"], list)
        assert isinstance(parsed["table_test"][0], dict)
        assert "final_concentration_ugml" in parsed["table_test"][0]
        assert isinstance(parsed["table_test"][1]["source_well"], Well)

    def test_blank_default(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Blank Defaults",
                "inputs": {
                    "int": "integer",
                    "str": "string",
                    "bool": "bool",
                    "decimal": "decimal",
                    "volume": "volume",
                    "temperature": "temperature",
                    "csv-table": "csv-table",
                },
            }
        )
        parsed = protocol_info.parse(self.protocol, {"refs": {}, "parameters": {}})
        assert parsed["int"] is None
        assert parsed["str"] is None
        assert parsed["bool"] is None
        assert parsed["decimal"] is None
        assert parsed["volume"] is None
        assert parsed["temperature"] is None
        assert isinstance(parsed["csv-table"], list)

    def test_ref_default(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Blank Defaults",
                "inputs": {
                    "aliquot": "aliquot",
                    "aliquot+": "aliquot+",
                    "aliquot++": "aliquot++",
                    "container": "container",
                    "container+": "container+",
                },
            }
        )
        parsed = protocol_info.parse(self.protocol, {"refs": {}, "parameters": {}})
        assert parsed["aliquot"] is None
        assert parsed["container"] is None
        assert isinstance(parsed["aliquot+"], WellGroup)
        assert 0 == len(parsed["aliquot+"])
        assert [] == parsed["aliquot++"]
        assert [] == parsed["container+"]

    def test_group_default(self):
        protocol_info = ProtocolInfo(
            {
                "name": "Test Basic Blank Defaults",
                "inputs": {
                    "group": {
                        "type": "group",
                        "inputs": {
                            "bool": "bool",
                            "aliquot": "aliquot",
                            "aliquot+": "aliquot+",
                        },
                    },
                    "group+": {"type": "group+", "inputs": {"bool": "bool"}},
                },
            }
        )
        parsed = protocol_info.parse(self.protocol, {"refs": {}, "parameters": {}})
        assert isinstance(parsed["group"], dict)
        assert parsed["group"]["bool"] is None
        assert parsed["group"]["aliquot"] is None
        assert isinstance(parsed["group"]["aliquot+"], WellGroup)
        assert 0 == len(parsed["group"]["aliquot+"])
        assert [{"bool": None}] == parsed["group+"]

    def test_container_errors(self):
        with pytest.raises(RuntimeError):
            protocol_info1 = ProtocolInfo(
                {"name": "Test Errors", "inputs": {"cont": {"type": "container"}}}
            )
            protocol_info1.parse(
                self.protocol,
                {
                    "refs": {"my_cont": {"type": "micro-1.5", "discard": True}},
                    "parameters": {"cont": "my_cont/0"},
                },
            )
        with pytest.raises(RuntimeError):
            protocol_info1 = ProtocolInfo(
                {"name": "Test Errors", "inputs": {"cont": {"type": "container"}}}
            )
            protocol_info1.parse(
                self.protocol,
                {
                    "refs": {"my_cont": {"type": "micro-1.5", "discard": True}},
                    "parameters": {"cont": "another_cont"},
                },
            )
        with pytest.raises(RuntimeError):
            protocol_info1 = ProtocolInfo(
                {"name": "Test Errors", "inputs": {"cont": {"type": "container"}}}
            )
            protocol_info1.parse(
                self.protocol,
                {
                    "refs": {"my_cont": {"type": "micro-1.5", "discard": True}},
                    "parameters": {"cont": 12},
                },
            )

    def test_container_volumes(self):
        protocol_info1 = ProtocolInfo(
            {
                "name": "Test Container Volumes",
                "inputs": {"cont": {"type": "container"}},
            }
        )
        parsed = protocol_info1.parse(
            self.protocol,
            {
                "refs": {
                    "echo_plate": {
                        "type": "384-echo",
                        "discard": True,
                        "aliquots": {"0": {"volume": "135:microliter"}},
                    }
                },
                "parameters": {"cont": "echo_plate"},
            },
        )
        assert parsed["cont"].well(0).volume == Unit(135, "microliter")

        with pytest.raises(ValueError) as e:
            protocol_info1.parse(
                self.protocol,
                {
                    "refs": {
                        "my_cont": {
                            "type": "384-echo",
                            "discard": True,
                            "aliquots": {"0": {"volume": "10000:microliter"}},
                        }
                    },
                    "parameters": {"cont": "my_cont"},
                },
            )
        assert "Theoretical volume" in str(e.value)

    # Test parsing of local manifest file
    def test_json_parse(self):
        with open("test/manifest_test.json", "r") as f:
            manifest_json = f.read()
            manifest = Manifest(json.loads(manifest_json))
            source = json.loads(manifest_json)["protocols"][0]["preview"]
            manifest.protocol_info("TestMethod").parse(self.protocol, source)

    def test_seal_on_store(self):
        seal_on_store(self.protocol)
        test = self.protocol.ref("test", None, "96-pcr", storage="cold_20")
        test2 = self.protocol.ref(
            "test2", None, "96-flat", storage="cold_20", cover="standard"
        )
        self.protocol.spin(test, "2000:g", "5:minute")
        self.protocol.spin(test2, "2000:g", "5:minute")
        assert len(self.protocol.instructions) == 3
        self.protocol.uncover(test2)
        seal_on_store(self.protocol)
        assert len(self.protocol.instructions) == 5
        assert self.protocol.instructions[-1].op == "cover"
        assert self.protocol.instructions[-1].lid == "low_evaporation"
        self.protocol.uncover(test2)
        seal_on_store(self.protocol)
        assert len(self.protocol.instructions) == 7
        assert self.protocol.instructions[-1].op == "cover"
        assert self.protocol.instructions[-1].lid == "low_evaporation"

    def test_seal_type_on_store(self):
        seal_on_store(self.protocol)
        test = self.protocol.ref("test", None, "384-pcr", storage="cold_20")
        self.protocol.seal(test, "foil")
        self.protocol.unseal(test)
        seal_on_store(self.protocol)
        assert self.protocol.instructions[-1].type == "ultra-clear"
        test2 = self.protocol.ref("test2", None, "384-pcr", storage="cold_20")
        self.protocol.seal(test2, "ultra-clear")
        self.protocol.unseal(test2)
        seal_on_store(self.protocol)
        assert self.protocol.instructions[-1].type == "ultra-clear"

    def test_cover_type_on_store(self):
        seal_on_store(self.protocol)
        test = self.protocol.ref("test", None, "96-flat-uv", storage="cold_20")
        self.protocol.cover(test, "universal")
        self.protocol.uncover(test)
        seal_on_store(self.protocol)
        assert self.protocol.instructions[-1].lid == "low_evaporation"
        test2 = self.protocol.ref("test2", None, "96-flat-uv", storage="cold_20")
        self.protocol.cover(test2)
        self.protocol.uncover(test2)
        seal_on_store(self.protocol)
        assert self.protocol.instructions[-1].lid == "low_evaporation"

    def test_get_protocol_preview(self):
        preview = get_protocol_preview(
            self.protocol, "TestMethod", manifest="test/manifest_test.json"
        )
        manifest_keys = [
            "my_string",
            "my_container",
            "my_volume",
            "my_length",
            "my_bool",
        ]
        for key in manifest_keys:
            assert key in preview
