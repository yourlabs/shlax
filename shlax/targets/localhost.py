import os

from shlax.proc import Proc

from ..strategies.script import Script


class Localhost(Script):
    root = '/'
