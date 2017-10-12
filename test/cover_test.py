import pytest
from autoprotocol.protocol import Protocol
from autoprotocol.harness import seal_on_store


class TestCoverSeal:
    def test_sequence_cover_instructions(self):
        p = Protocol()
        cont1 = p.ref("c1", None, "384-pcr", storage="cold_4")
        cont2 = p.ref("c2", None, "384-pcr", storage="cold_4")
        cont3 = p.ref("c3", None, "96-deep", storage="cold_4")
        cont4 = p.ref("c4", None, "micro-1.5", storage="cold_4")
        cont5 = p.ref("c5", None, "384-echo", discard=True)
        therm_groups = [
            {
                "cycles": 1,
                "steps": [
                    {
                        "temperature": "37:celsius",
                        "duration": "60:minute"
                    },
                ]
            }
        ]
        p.incubate(cont1, "ambient", duration="1:minute")
        assert (p.instructions[0].op == "seal")
        assert (p.instructions[1].op == "incubate")
        assert (cont1.cover == "ultra-clear")

        p.spin(cont1, acceleration="1000:g", duration="2:minute")
        assert (cont1.cover == "ultra-clear")
        assert (cont2.cover is None)

        p.thermocycle(cont2, groups=therm_groups)
        assert (cont2.cover == "ultra-clear")

        p.transfer(cont2.well(0), cont1.well(1), volume="1:microliter")
        assert (cont1.cover is None)
        assert (cont2.cover is None)
        with pytest.raises(RuntimeError):
            p.cover(cont2)

        p.seal(cont2)
        p.thermocycle(cont1, groups=therm_groups)
        assert (cont1.cover == "ultra-clear")

        p.spin(cont1, acceleration="1000:g", duration="2:minute")
        p.spin(cont2, acceleration="1000:g", duration="2:minute")
        p.spin(cont5, acceleration="1000:g", duration="2:minute")
        assert (cont1.cover == "ultra-clear")
        assert (cont2.cover == "ultra-clear")
        assert (cont5.cover == "universal")

        p.uncover(cont5)
        p.unseal(cont1)
        p.transfer(cont4.well(0), cont3.well(0), "1:microliter")
        p.spin(cont4, acceleration="1000:g", duration="2:minute")
        assert (cont4.cover is None)
        with pytest.raises(RuntimeError):
            p.thermocycle(cont4, groups=therm_groups)

        seal_on_store(p)
        assert (cont1.cover == "ultra-clear")
        assert (cont2.cover == "ultra-clear")
        assert (cont3.cover == "standard")
        assert (cont4.cover is None)
        assert (cont5.cover is None)

    def test_sequence_cover_instructions2(self):
        p = Protocol()
        cont1 = p.ref("c1", None, "96-pcr", storage="cold_4")
        p.incubate(cont1, "ambient", duration="1:minute")
        assert (p.instructions[0].op == "seal")

        cont2 = p.ref("c2", None, "96-pcr", storage="cold_4")
        p.incubate(cont2, "ambient", duration="1:minute", uncovered=True)
        assert (p.instructions[-2].op == "incubate")
        with pytest.raises(RuntimeError):
            p.incubate(cont1, "cold_4", duration="1:minute", uncovered=True)
