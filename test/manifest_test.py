import unittest
from autoprotocol.harness import ProtocolInfo, run, Manifest
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

    def test_errors(self):
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
                },
                'group+': {
                    'type': 'group+',
                    'inputs': {
                        'bool': 'bool'
                    }
                }
            }
            })
            parsed1 = protocol_info1.parse(self.protocol, {
                'refs': {},
                'parameters': {}
            })

    # Test parsing of local manifest file
    def test_json_parse(self):
        protocol = Protocol()
        manifest_json = open('test/manifest_test.json', 'r').read()
        manifest = Manifest(json.loads(manifest_json))
        source = json.loads(manifest_json)['protocols'][0]['preview']
        params = manifest.protocol_info('TestMethod').parse(protocol, source)
