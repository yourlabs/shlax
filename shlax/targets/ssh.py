import os

from shlax.proc import Proc

from .localhost import Localhost


class Ssh(Localhost):
    root = '/'

    def __init__(self, host, *args, **kwargs):
        self.host = host
        super().__init__(*args, **kwargs)

    def shargs(self, *args, **kwargs):
        args, kwargs = super().shargs(*args, **kwargs)
        return (['ssh', self.host] + list(args)), kwargs
