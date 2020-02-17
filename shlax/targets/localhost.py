import os
import re

from shlax.proc import Proc

from ..strategies.script import Script


class Localhost(Script):
    root = '/'
    contextualize = Script.contextualize + ['home']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.home = kwargs.pop('home', os.getcwd())

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

        if self.parent:
            return self.parent.shargs(*args, **kwargs)
        else:
            return args, kwargs

    async def exec(self, *args, **kwargs):
        if 'debug' not in kwargs:
            kwargs['debug'] = getattr(self, 'call_kwargs', {}).get('debug', False)
        kwargs.setdefault('output', self.output)
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

    async def exists(self, *paths):
        proc = await self.exec('type ' + ' '.join(cmd), raises=False)

    async def which(self, *cmd):
        """
        Return the first path to the cmd in the container.

        If cmd argument is a list then it will try all commands.
        """
        proc = await self.exec('type ' + ' '.join(cmd), raises=False)
        result = []
        for res in proc.out.split('\n'):
            match = re.match('([^ ]+) is ([^ ]+)$', res.strip())
            if match:
                result.append(match.group(1))
        return result

    async def copy(self, *args):
        if args[-1].startswith('./'):
            args = list(args)
            args[-1] = self.home + '/' + args[-1][2:]
        args = ['cp', '-rua'] + list(args)
        return await self.exec(*args)

    async def mount(self, *dirs):
        pass

    async def mkdir(self, *dirs):
        return await self.exec(*['mkdir', '-p'] + list(dirs))
