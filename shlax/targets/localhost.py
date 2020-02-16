import copy
import re

from ..output import Output
from ..proc import Proc
from ..result import Result, Results

from .base import Target


class Localhost(Target):
    def shargs(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        args = [str(arg) for arg in args if args is not None]

        if args and ' ' in args[0]:
            if len(args) == 1:
                args = ['sh', '-euc', args[0]]
            else:
                args = ['sh', '-euc'] + list(args)

        if user == 'root':
            args = ['sudo'] + args
        elif user:
            args = ['sudo', '-u', user] + args

        return args, kwargs

        if self.parent:
            return self.parent.shargs(*args, **kwargs)
        else:
            return args, kwargs

    async def exec(self, *args, **kwargs):
        kwargs['output'] = self.output
        args, kwargs = self.shargs(*args, **kwargs)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc
