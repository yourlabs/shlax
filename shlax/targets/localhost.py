import os

from shlax.proc import Proc

from ..strategies.script import Script


class Localhost(Script):
    root = '/'

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
        kwargs.setdefault('debug', self.call_kwargs.get('debug', False))
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
