import re


class Compound:
    """
    Represents a single Compound

    Parameters
    ----------
    comp_format : Compound string input format
    value : Compound string

    """

    def __init__(self, comp_format, value):
        compound_formats = ["Daylight Canonical SMILES", "InChI"]
        if comp_format in compound_formats:
            self.format = comp_format
        else:
            raise CompoundError(f"{comp_format} is not an acceptable Compound format.")

        if self.is_valid(value):
            self.value = value
        else:
            raise CompoundError(f"{value} is not a valid {self.format} value.")

    def is_valid(self, compound):
        inchi_pattern = r"^InChI\=1S?\/[^\s]+(\s|$)"
        non_inchi_pattern = r"^(?!InChI=)\w\S+$"

        if self.format == "InChI":
            return bool(re.match(inchi_pattern, compound))
        elif self.format == "Daylight Canonical SMILES":
            return bool(
                re.match(non_inchi_pattern, compound)
                and not re.search("[~?!$%^&;'Jj]", compound)
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
