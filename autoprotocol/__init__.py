from .container import Container, Well, WellGroup  # NOQA
from .container_type import ContainerType  # NOQA
from .protocol import Protocol  # NOQA
from .unit import Unit  # NOQA


class UserError(Exception):
    """Will result in a nice message being displayed to the user."""

    def __init__(self, message, info=None):
        super(UserError, self).__init__(message)
        self.info = info

    @property
    def message(self):
        return str(self)
