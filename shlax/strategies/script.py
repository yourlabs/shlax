import copy
import os

from ..exceptions import WrongResult
from ..actions.base import Action
from ..proc import Proc


class Actions(list):
    def __init__(self, owner, actions):
        self.owner = owner
        super().__init__()
        for action in actions:
            self.append(action)

    def append(self, value):
        value = copy.deepcopy(value)
        value.parent = self.owner
        value.status = 'pending'
        super().append(value)


class Script(Action):
    root = '/'
    contextualize = ['shargs', 'exec', 'rexec', 'env', 'which', 'copy']

    def __init__(self, *actions, **kwargs):
        super().__init__(**kwargs)
        self.actions = Actions(self, actions)

    async def call(self, *args, **kwargs):
        for action in self.actions:
            await action(*args, **kwargs)

    def shargs(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        kwargs['debug'] = True
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

        if self.parent:
            return self.parent.shargs(*args, **kwargs)
        else:
            return args, kwargs

    async def exec(self, *args, **kwargs):
        args, kwargs = self.shargs(*args, **kwargs)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc

    async def rexec(self, *args, **kwargs):
        kwargs['user'] = 'root'
        return await self.exec(*args, **kwargs)

    async def env(self, name):
        return (await self.exec('echo $' + name)).out

    async def which(self, *cmd):
        """
        Return the first path to the cmd in the container.

        If cmd argument is a list then it will try all commands.
        """
        for path in (await self.env('PATH')).split(':'):
            for c in cmd:
                p = os.path.join(self.root, path[1:], c)
                if os.path.exists(p):
                    return p[len(str(self.root)):]

    async def copy(self, *args):
        args = ['cp', '-ra'] + list(args)
        return await self.exec(*args)
