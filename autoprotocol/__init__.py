from .container import Container, Well, WellGroup
from .protocol import Protocol
from .container_type import ContainerType
from .unit import Unit


class UserError(Exception):
    '''Will result in a nice message being displayed to the user.'''
    def __init__(self, message, info=None):
        super(Exception, self).__init__(message)
        self.info = info
