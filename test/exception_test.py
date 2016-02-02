import unittest

from autoprotocol import UserError


class TestUserError(unittest.TestCase):
    def test_catch(self):
        with self.assertRaises(UserError):
            raise UserError("spam")
        try:
            raise UserError("eggs")
        except UserError as e:
            self.assertIn("eggs", str(e))
