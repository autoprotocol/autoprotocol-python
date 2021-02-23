# pragma pylint: disable=missing-docstring
import pytest

from autoprotocol.compound import Compound
from autoprotocol.container import WellGroup
from autoprotocol.informatics import AttachCompounds
from autoprotocol.protocol import Protocol


# pylint: disable=protected-access
class TestAttachCompoundsInformatics(object):
    def test_attach_compounds(self):
        p = Protocol()
        cont1 = p.ref("cont_1", None, "96-flat", discard=True)
        well1 = cont1.well(0)
        well2 = cont1.well(1)
        wg1 = WellGroup([well1, well2])
        comp1 = Compound("InChI=1S/CH4/h1H4")
        comp2 = Compound("InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3")

        assert AttachCompounds(well1, [comp1]).compounds == [comp1]
        assert AttachCompounds(well1, [comp1]).wells == well1
        assert AttachCompounds(wg1, [comp1, comp2]).compounds == [comp1, comp2]
        assert AttachCompounds(wg1, [comp1, comp2]).wells == wg1

    def test_as_dict(self):
        p = Protocol()
        cont1 = p.ref("cont_1", None, "96-flat", discard=True)
        well1 = WellGroup([cont1.well(0)])
        comp = Compound("InChI=1S/CH4/h1H4")
        assert AttachCompounds(well1, [comp]).as_dict() == {
            "type": "attach_compounds",
            "data": {"wells": well1, "compounds": [comp]},
        }

    def test_validate(self):
        p = Protocol()
        cont1 = p.ref("cont_1", None, "96-flat", discard=True)
        well1 = WellGroup([cont1.well(0)])
        comp = Compound("InChI=1S/CH4/h1H4")
        with pytest.raises(TypeError):
            AttachCompounds(well1, comp)
        with pytest.raises(TypeError):
            AttachCompounds("foo", [comp])
        with pytest.raises(TypeError):
            AttachCompounds(well1, "InChI=1S/CH4/h1H4")
