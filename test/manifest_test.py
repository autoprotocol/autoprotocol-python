import unittest
from autoprotocol.harness import ProtocolInfo, run, Manifest, seal_on_store
from autoprotocol import Protocol, Unit, Well, WellGroup
import json


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.protocol = Protocol()

    def test_empty(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Empty',
            'inputs': {}
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {},
            'parameters': {}
        })
        self.assertEqual({}, parsed)

    def test_basic_types(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Types',
            'inputs': {
                'bool': 'bool',
                'string': 'string',
                'integer': 'integer',
                'decimal': 'decimal'
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {},
            'parameters': {
                'bool': True,
                'string': 'test',
                'integer': 3,
                'decimal': 2.1
            }
        })
        self.assertEqual({
            'bool': True,
            'string': 'test',
            'integer': 3,
            'decimal': 2.1
        }, parsed)
        with self.assertRaises(RuntimeError):
            parsed = protocol_info.parse(self.protocol, {
                'refs': {},
                'parameters': {
                    'bool': True,
                    'string': 'test',
                    'integer': "hi",
                    'decimal': 2.1
                }
            })
            parsed = protocol_info.parse(self.protocol, {
                'refs': {},
                'parameters': {
                    'bool': True,
                    'string': 'test',
                    'integer': "3",
                    'decimal': "hi"
                }
            })

    def test_unit_types(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Types',
            'inputs': {
                'volume': 'volume',
                'time': 'time',
                'temperature': 'temperature'
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {},
            'parameters': {
                'volume': '3:microliter',
                'time': '30:second',
                'temperature': '25:celsius'
            }
        })
        self.assertEqual({
            'volume': Unit.fromstring('3:microliter'),
            'time': Unit.fromstring('30:second'),
            'temperature': Unit.fromstring('25:celsius')
        }, parsed)
        with self.assertRaises(RuntimeError):
            parsed = protocol_info.parse(self.protocol, {
                'refs': {},
                'parameters': {
                    'volume': 3,
                    'time': '30:second',
                    'temperature': '25:celsius'
                    }
                })
            parsed = protocol_info.parse(self.protocol, {
                'refs': {},
                'parameters': {
                    'volume': "3:microliter",
                    'time': "hello",
                    'temperature': '25:celsius'
                    }
                })
            parsed = protocol_info.parse(self.protocol, {
                'refs': {},
                'parameters': {
                    'volume': "3:microliter",
                    'time': "30:second",
                    'temperature': 25
                    }
                })

    def test_group(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Types',
            'inputs': {
                'group_test': {
                    'type': 'group',
                    'inputs': {
                        'test': 'aliquot'
                    }
                }
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {
                'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
            },
            'parameters': {
                'group_test': {
                    'test': 'ct1test/0'
                }
            }
        })
        self.assertTrue(isinstance(parsed['group_test'], dict))
        self.assertTrue('test' in parsed['group_test'])
        self.assertTrue(isinstance(parsed['group_test']['test'], Well))
        with self.assertRaises(RuntimeError):
            protocol_info1 = ProtocolInfo({
            'name': 'Test Errors',
            'inputs': {
                'group': {
                    'type': 'group',
                    'inputs': {
                        'bool': 'bool',
                        'aliquot': 'aliquot',
                        'aliquot+': 'aliquot+'
                    }
                }
            }})
            parsed1 = protocol_info1.parse(self.protocol, {
                'refs': {
                },
                'parameters': {
                    'group': ["hello"]
                }
            })
            protocol_info2 = ProtocolInfo({
            'name': 'Test Errors',
            'inputs': {
                'group': {
                    'type': 'group'
                }
            }})
            parsed2 = protocol_info2.parse(self.protocol, {
                'refs': {
                },
                'parameters': {
                    'group': {
                        "bool": True,
                        "aliquot": "dummy/0",
                        "aliquot+": ["dummy/0"]
                    }
                }
            })


    def test_multigroup(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Types',
            'inputs': {
                'group_test': {
                    'type': 'group+',
                    'inputs': {
                        'test': 'aliquot'
                    }
                }
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {
                'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
            },
            'parameters': {
                'group_test': [
                    {'test': 'ct1test/0'},
                    {'test': 'ct1test/1'}
                ]
            }
        })
        self.assertTrue(isinstance(parsed['group_test'], list))
        self.assertEqual(2, len(parsed['group_test']))
        self.assertTrue('test' in parsed['group_test'][0])
        self.assertTrue(isinstance(parsed['group_test'][0]['test'], Well))
        self.assertTrue('test' in parsed['group_test'][1])
        self.assertTrue(isinstance(parsed['group_test'][1]['test'], Well))
        self.assertEqual(1, parsed['group_test'][1]['test'].index)
        with self.assertRaises(RuntimeError):
            parsed = protocol_info.parse(self.protocol, {
            'refs': {
                'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
            },
            'parameters': {
                'group_test': {
                    'test': 'ct1test/0',
                    'test': 'ct1test/1'
                    }
                }
            })
            protocol_info = ProtocolInfo({
            'name': 'Test Basic Types',
            'inputs': {
                'group_test': {
                    'type': 'group+'
                }
            }
            })
            parsed = protocol_info.parse(self.protocol, {
                'refs': {
                    'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
                },
                'parameters': {
                    'group_test': [
                        {'test': 'ct1test/0'},
                        {'test': 'ct1test/1'}
                    ]
                }
            })

    def test_group_choice(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Types',
            'inputs': {
                'group_test': {
                    'type': 'group-choice',
                    'options': [
                        {
                            'value': 'a',
                            'inputs': {
                                'test': 'aliquot'
                            }
                        },
                        {
                            'value': 'b'
                        }
                    ]
                }
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {
                'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
            },
            'parameters': {
                'group_test': {
                    'value': 'a',
                    'inputs': {
                        'a': {
                            'test': 'ct1test/0'
                        },
                        'b': {
                        }
                    }
                }
            }
        })
        self.assertTrue(isinstance(parsed['group_test'], dict))
        self.assertEqual('a', parsed['group_test']['value'])
        self.assertTrue('a' in parsed['group_test']['inputs'])
        self.assertFalse('b' in parsed['group_test']['inputs'])
        self.assertTrue(
            isinstance(parsed['group_test']['inputs']['a']['test'], Well))
        with self.assertRaises(RuntimeError):
            parsed = protocol_info.parse(self.protocol, {
                'refs': {
                    'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
                },
                'parameters': {
                    'group_test': {
                        'value': 'a'
                    }
                }
            })
            parsed = protocol_info.parse(self.protocol, {
                'refs': {
                    'ct1test': {'id': 'ct1test', 'type': '96-pcr', 'discard': True}
                },
                'parameters': {
                    'group_test': {
                        'inputs': {
                            'a': {
                                'test': 'ct1test/0'
                            },
                            'b': {
                            }
                        }
                    }
                }
            })

    def test_blank_default(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Blank Defaults',
            'inputs': {
                'int': 'integer',
                'str': 'string',
                'bool': 'bool',
                'decimal': 'decimal',
                'volume': 'volume',
                'temperature': 'temperature',
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {},
            'parameters': {}
        })
        self.assertIsNone(parsed['int'])
        self.assertIsNone(parsed['str'])
        self.assertIsNone(parsed['bool'])
        self.assertIsNone(parsed['decimal'])
        self.assertIsNone(parsed['volume'])
        self.assertIsNone(parsed['temperature'])

    def test_ref_default(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Blank Defaults',
            'inputs': {
                'aliquot': 'aliquot',
                'aliquot+': 'aliquot+',
                'aliquot++': 'aliquot++',
                'container': 'container',
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {},
            'parameters': {}
        })
        self.assertIsNone(parsed['aliquot'])
        self.assertIsNone(parsed['container'])
        self.assertIsInstance(parsed['aliquot+'], WellGroup)
        self.assertEqual(0, len(parsed['aliquot+']))
        self.assertEqual([], parsed['aliquot++'])

    def test_group_default(self):
        protocol_info = ProtocolInfo({
            'name': 'Test Basic Blank Defaults',
            'inputs': {
                'group': {
                    'type': 'group',
                    'inputs': {
                        'bool': 'bool',
                        'aliquot': 'aliquot',
                        'aliquot+': 'aliquot+'
                    }
                },
                'group+': {
                    'type': 'group+',
                    'inputs': {
                        'bool': 'bool'
                    }
                }
            }
        })
        parsed = protocol_info.parse(self.protocol, {
            'refs': {},
            'parameters': {}
        })
        self.assertIsInstance(parsed['group'], dict)
        self.assertIsNone(parsed['group']['bool'])
        self.assertIsNone(parsed['group']['aliquot'])
        self.assertIsInstance(parsed['group']['aliquot+'], WellGroup)
        self.assertEqual(0, len(parsed['group']['aliquot+']))
        self.assertEqual([{'bool': None}], parsed['group+'])


    def test_container_errors(self):
        with self.assertRaises(RuntimeError):
            protocol_info1 = ProtocolInfo({
            'name': 'Test Errors',
            'inputs': {
                'cont': {
                    'type': 'container'
                }
            }})
            parsed1 = protocol_info1.parse(self.protocol, {
                'refs': {
                    "my_cont":{
                        "type": "micro-1.5",
                        "discard": True
                    }
                },
                'parameters': {
                    "cont": "my_cont/0"
                }
            })
            parsed2 = protocol_info1.parse(self.protocol, {
                'refs': {
                    "my_cont":{
                        "type": "micro-1.5",
                        "discard": True
                    }
                },
                'parameters': {
                    "cont": "another_cont"
                }
            })
            parsed3 = protocol_info1.parse(self.protocol, {
                'refs': {
                    "my_cont":{
                        "type": "micro-1.5",
                        "discard": True
                    }
                },
                'parameters': {
                    "cont": 12
                }
            })



    # Test parsing of local manifest file
    def test_json_parse(self):
        protocol = Protocol()
        manifest_json = open('test/manifest_test.json', 'r').read()
        manifest = Manifest(json.loads(manifest_json))
        source = json.loads(manifest_json)['protocols'][0]['preview']
        params = manifest.protocol_info('TestMethod').parse(protocol, source)

    def test_seal_on_store(self):
        seal_on_store(self.protocol)
        test = self.protocol.ref("test", None, "96-pcr", storage="cold_20")
        test2 = self.protocol.ref("test2", None, "96-flat", storage="cold_20",
                                  cover="standard")
        self.protocol.spin(test, "2000:g", "5:minute")
        self.protocol.spin(test2, "2000:g", "5:minute")
        self.assertEqual(len(self.protocol.instructions), 2)
        seal_on_store(self.protocol)
        self.assertEqual(len(self.protocol.instructions), 3)
        self.assertTrue(self.protocol.instructions[-1].op == "seal")
        self.assertTrue(self.protocol.refs["test"].opts.get("cover"))
        self.assertTrue(self.protocol.refs["test2"].opts.get("cover"))
        self.protocol.uncover(test2)
        seal_on_store(self.protocol)
        self.assertEqual(len(self.protocol.instructions), 5)
        self.assertTrue(self.protocol.instructions[-1].op == "cover")

