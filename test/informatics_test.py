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
        wg1 = WellGroup([cont1.well(0), cont1.well(1)])
        wg2 = WellGroup([cont1.well(2), cont1.well(3)])
        comp = Compound("InChI=1S/CH4/h1H4")

        assert AttachCompounds(
            {"wells": well1, "compounds": [comp]}, wg1
        ).compounds == [comp]
        assert (
            AttachCompounds({"wells": well1, "compounds": [comp]}, wg1).wells == well1
        )
        with pytest.raises(TypeError):
            AttachCompounds("foo", wg1)
        with pytest.raises(KeyError):
            AttachCompounds({"foo": well1, "compounds": [comp]}, wg1)
        with pytest.raises(KeyError):
            AttachCompounds({"wells": well1, "bar": [comp]}, wg1)
        with pytest.raises(TypeError):
            AttachCompounds({"wells": "cont_1/0", "compounds": [comp]}, wg1)
        with pytest.raises(ValueError):
            AttachCompounds({"wells": well1, "compounds": [comp]}, wg2)
        with pytest.raises(TypeError):
            AttachCompounds({"wells": well1, "compounds": comp}, wg1)
        with pytest.raises(TypeError):
            AttachCompounds({"wells": well1, "compounds": "foo"}, wg1)

    def test_as_dict(self):
        p = Protocol()
        cont1 = p.ref("cont_1", None, "96-flat", discard=True)
        well1 = WellGroup([cont1.well(0)])
        comp = Compound("InChI=1S/CH4/h1H4")
        example_informatics = {"wells": well1, "compounds": [comp]}
        assert AttachCompounds(example_informatics, well1).as_dict() == {
            "type": "attach_compounds",
            "data": {"wells": well1, "compounds": [comp]},
        }
