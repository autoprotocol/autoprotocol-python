import re


class Compound:
    """
    Represents a single Compound

    Parameters
    ----------
    InChI : Standard International Chemical Identifier

    """

    def __init__(self, InChI):
        if self.is_valid(InChI):
            self.InChI = InChI
        else:
            raise CompoundError(f"{InChI} is not a valid InChI key")

    @staticmethod
    def is_valid(InChI):
        pattern = r"^InChI\=1S?\/[^\s]+(\s|$)"
        return re.match(pattern, InChI)


class CompoundError(Exception):
    def __init__(self, value):
        super(CompoundError, self).__init__(value)
        self.value = value
