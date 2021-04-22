import re


class Compound:
    """
    Represents a single Compound

    Parameters
    ----------
    format : Compound string input format
    value : Compound string

    """

    # pragma pylint: disable=redefined-builtin
    def __init__(self, format, value):
        compound_formats = ["Daylight Canonical SMILES", "InChI"]
        if format in compound_formats:
            self.format = format
        else:
            raise CompoundError(f"{format} is not an acceptable Compound format.")

        if self.is_valid(value):
            self.value = value
        else:
            raise CompoundError(f"{value} is not a valid {self.format} value.")

    def is_valid(self, compound):
        inchi_pattern = r"^InChI\=1S?\/[^\s]+(\s|$)"
        non_inchi_pattern = r"^(?!InChI=)\w\S+$"
        non_smiles_pattern = "[~?!$%^&;'J]"

        if self.format == "InChI":
            return bool(re.match(inchi_pattern, compound))
        elif self.format == "Daylight Canonical SMILES":
            return bool(
                re.match(non_inchi_pattern, compound)
                and not re.search(non_smiles_pattern, compound)
            )
        else:
            raise CompoundError(
                f"String pattern is not defined for this compound format: {self.format}."
            )

    def as_dict(self):
        """generates a Python object representation of Compound

        Returns
        -------
        dict
            a dict of python objects that have the same structure as the
            Autoprotocol JSON for the Compound

        Notes
        -----
        Used as a part of JSON serialization of the Compound

        """

        return {
            "format": self.format,
            "value": self.value,
        }


class CompoundError(Exception):
    def __init__(self, value):
        super(CompoundError, self).__init__(value)
        self.value = value
