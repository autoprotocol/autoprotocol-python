import unittest
from autoprotocol.harness import ProtocolInfo
from autoprotocol import Protocol, Unit, Well


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
