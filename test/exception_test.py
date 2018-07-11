import pytest
from autoprotocol import UserError


class TestUserError(object):
    def test_catch(self):
        with pytest.raises(UserError):
            raise UserError("spam")

        try:
            raise UserError("eggs")
        except UserError as e:
            assert "eggs" in e.message

        e = UserError("Test")
        assert e.message == "Test"
