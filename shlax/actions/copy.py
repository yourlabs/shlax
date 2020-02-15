from .base import Action


class Copy(Action):
    def __init__(self, *args):
        self.src = args[:-1]
        self.dst = args[-1]

    def call(self, *args, **kwargs):
        self.copy(self.src, self.dst)
