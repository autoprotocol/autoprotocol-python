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
        comp = Compound("InChI=1S/CH4/h1H4")

        assert AttachCompounds({"wells": well1, "compounds": [comp]}).compounds == [
            comp
        ]
        assert AttachCompounds({"wells": well1, "compounds": [comp]}).wells == well1
        with pytest.raises(TypeError):
            AttachCompounds("foo")
        with pytest.raises(KeyError):
            AttachCompounds({"foo": well1, "compounds": [comp]})
        with pytest.raises(KeyError):
            AttachCompounds({"wells": well1, "bar": [comp]})

    def test_as_dict(self):
        p = Protocol()
        cont1 = p.ref("cont_1", None, "96-flat", discard=True)
        well1 = WellGroup([cont1.well(0)])
        comp = Compound("InChI=1S/CH4/h1H4")
        example_informatics = {"wells": well1, "compounds": [comp]}
        assert AttachCompounds(example_informatics).as_dict() == {
            "type": "attach_compounds",
            "data": {"wells": well1, "compounds": [comp]},
        }

    def test_validate(self):
        p = Protocol()
        cont1 = p.ref("cont_1", None, "96-flat", discard=True)
        well1 = WellGroup([cont1.well(0)])
        comp = Compound("InChI=1S/CH4/h1H4")
        with pytest.raises(TypeError):
            AttachCompounds({"wells": "foo", "compounds": [comp]}).validate()
        with pytest.raises(TypeError):
            AttachCompounds({"wells": well1, "compounds": comp}).validate()
        with pytest.raises(TypeError):
            AttachCompounds({"wells": well1, "compounds": "foo"}).validate()
