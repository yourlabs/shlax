
from .targets import Localhost


class Play:
    def __init__(self, *actions, targets=None, options=None):
        self.options = options or {}
        self.targets = targets or dict(localhost=Localhost())
        self.actions =
