# pragma pylint: disable=missing-docstring,attribute-defined-outside-init
import warnings
import pytest
from autoprotocol.container import Container


class HasDummyWell(object):
    @pytest.fixture(autouse=True)
    def make_wells(self, dummy_type):
        self.container = Container(id=None, container_type=dummy_type)
        self.well = self.container.well(0)


class TestValidateProperties(HasDummyWell):
    def test_rejects_incorrect_types(self):
        with pytest.raises(TypeError):
            self.well.set_properties(["property", "value"])
        with pytest.raises(TypeError):
            self.well.set_properties({"property", True})
        with pytest.raises(TypeError):
            self.well.set_properties({("property"), "value"})

    def test_can_use_nonstring_properties(self):
        self.well.set_properties({"foo": [1, 2, 3]})
        self.well.add_properties({"bar": [1, 2, 3]})

    def test_fails_to_set_unserializable_property(self):
        with pytest.raises(TypeError):
            self.well.set_properties({"test": {1}})


class TestSetProperties(HasDummyWell):
    def test_sets_properties(self):
        test_property = {"foo": "bar"}
        self.well.set_properties(test_property)
        assert self.well.properties == test_property

    def test_overwrites_properties(self):
        new_property = {"bar": True}
        self.well.set_properties({"foo": True})
        self.well.set_properties(new_property)
        assert self.well.properties == new_property


class TestAddProperties(HasDummyWell):
    def test_adds_properties(self):
        test_property = {"foo": "bar"}
        self.well.set_properties(test_property)
        assert self.well.properties == test_property

    def test_doesnt_overwrite_properties(self):
        old_property = {"foo": True}
        new_property = {"bar": False}
        self.well.add_properties(old_property)
        self.well.add_properties(new_property)
        merged_properties = old_property.copy()
        merged_properties.update(new_property)
        assert self.well.properties == merged_properties

    def test_add_properties_appends_lists(self):
        self.well.set_properties({"foo": ["bar"]})
        self.well.add_properties({"foo": ["baz"]})
        assert self.well.properties == {"foo": ["bar", "baz"]}

    def test_warns_when_overwriting_property(self):
        with warnings.catch_warnings(record=True) as w:
            self.well.set_properties({"foo": "bar"})
            self.well.add_properties({"foo": "bar"})
            assert len(w) == 1
            for message in w:
                assert "Overwriting existing property" in str(message.message)

    def test_doesnt_warn_when_not_overwriting_property(self):
        with warnings.catch_warnings(record=True) as w:
            self.well.set_properties({"field1": True})
            self.well.add_properties({"field2": False})
            assert len(w) == 0
