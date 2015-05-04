
import unittest

from autoprotocol import util

class UtilTestCase(unittest.TestCase):
    def test_make_dottable_dict(self):
        sample = {
            "forks": 6,
            "spoons": 5,
            "knives": 3
        }

        sample = util.make_dottable_dict(sample)

        self.assertEqual(
            sample.forks,
            6,
        )

        sample.sporks = 2
        self.assertEqual(
            sample.sporks,
            2,
        )

        del sample.spoons
        self.assertEqual(
            len(sample),
            3,
        )
        with self.assertRaises(KeyError):
            sample.spoons

    def test_deep_merge_params(self):
        defaults = {
            "forks": 1,
            "knives": 2,
        }
        override = {
            "forks": 2,
            "spoons": 3,
        }
        merged = util.deep_merge_params(
            defaults,
            override,
        )
        self.assertEqual(
            merged.forks,
            2,
        )
        self.assertEqual(
            merged.knives,
            2,
        )
        self.assertEqual(
            merged.spoons,
            3,
        )

    def test_deep_merge_params_inception(self):
        defaults = {
            "a": {
                "b": 1,
                "c": 2,
            },
            # d is in defaults, but not override
            "d": {
                "e": 3,
            },
        }
        override = {
            # a is in both override and defaults
            "a": {
                "b": 4,
            },
            # f is in override, but not defaults
            "f": {
                "g": 5,
            },
        }
        merged = util.deep_merge_params(
            defaults,
            override,
        )
        self.assertEqual(
            merged,
            {
                "a": {
                    "b": 4,
                    "c": 2,
                },
                "d": {
                    "e": 3,
                },
                "f": {
                    "g": 5,
                },
            },
        )
