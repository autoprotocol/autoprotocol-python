import pytest
from autoprotocol import UserError


class TestUserError:
    def test_catch(self):
        with pytest.raises(UserError):
            raise UserError("spam")

        with pytest.raises(UserError) as e:
            raise UserError("eggs")
            assert "eggs" in e.value

        e = UserError("Test")
        assert e.message == "Test"
