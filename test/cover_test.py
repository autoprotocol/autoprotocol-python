import pytest
from autoprotocol.protocol import Protocol


class TestCoverSeal(object):
    def test_sequence_cover_instructions2(self):
        p = Protocol()
        cont1 = p.ref("c1", None, "96-pcr", storage="cold_4")
        p.incubate(cont1, "ambient", duration="1:minute")
        assert p.instructions[0].op == "seal"

        cont2 = p.ref("c2", None, "96-pcr", storage="cold_4")
        p.incubate(cont2, "ambient", duration="1:minute", uncovered=True)
        assert p.instructions[-2].op == "incubate"
        with pytest.raises(RuntimeError):
            p.incubate(cont1, "cold_4", duration="1:minute", uncovered=True)
