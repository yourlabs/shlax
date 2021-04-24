import asyncio
import copy
from pathlib import Path
import os
import re
import sys

from ..output import Output
from ..proc import Proc, ProcFailure
from ..result import Result, Results


class Target:
    isguest = False

    def __init__(self, *actions, root=None):
        self.actions = actions
        self.results = []
        self.output = Output()
        self.parent = None
        self.root = root or ''

    def __str__(self):
        return 'localhost'

    @property
    def parent(self):
        return self._parent or Target()

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def caller(self):
        """Traverse parents and return the top-levels Target."""
        if not self._parent:
            return self
        caller = self._parent
        while caller._parent:
            caller = caller._parent
        return caller

    async def __call__(self, *actions, target=None):
        if target:
            # that's going to be used by other target methods, to access
            # the calling target
            self.parent = target

        result = Result(self, self)
        result.status = 'success'

        for action in actions or self.actions:
            if await self.action(action, reraise=bool(actions)):
                result.status = 'failure'
                break

        if getattr(self, 'clean', None):
            self.output.clean(self)
            await self.clean(self, result)

    async def action(self, action, reraise=False):
        result = Result(self, action)
        self.output.start(action)
        try:
            await action(target=self)
        except Exception as e:
            self.output.fail(action, e)
            result.status = 'failure'
            result.exception = e

            if not isinstance(e, ProcFailure):
                # no need to reraise in case of command error
                # because the command has been printed

                if reraise:
                    # nested call, re-raise
                    raise
                else:
                    import traceback
                    traceback.print_exception(type(e), e, sys.exc_info()[2])

            return True  # because it failed
        else:
            if getattr(action, 'skipped', False):
                self.output.skip(action)
            else:
                self.output.success(action)
            result.status = 'success'
        finally:
            self.caller.results.append(result)

            clean = getattr(action, 'clean', None)
            if clean:
                self.output.clean(action)
                await clean(self, result)

    async def rexec(self, *args, **kwargs):
        kwargs['user'] = 'root'
        return await self.exec(*args, **kwargs)

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

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, value):
        self._root = Path(value) if value else ''

    @property
    def host(self):
        current = self
        while current.isguest:
            current = self.parent
        return current

    def path(self, path):
        if not self.root:
            return path
        if str(path).startswith('/'):
            path = str(path)[1:]
        return str(self.root / path)

    async def mkdir(self, *paths):
        if '_mkdir' not in self.__dict__:
            self._mkdir = []

        make = [str(path) for path in paths if str(path) not in self._mkdir]
        if make:
            await self.exec('mkdir', '-p', *make)
            self._mkdir += make

    async def copy(self, *args):
        return await self.exec('cp', '-a', *args)

    async def exists(self, path):
        return (await self.exec('ls ' + self.path(path), raises=False)).rc == 0

    async def read(self, path):
        return (await self.exec('cat', self.path(path))).out

    async def write(self, path, content, **kwargs):
        return await self.exec(
            f'cat > {self.path(path)} <<EOF\n'
            + content
            + '\nEOF',
            **kwargs
        )

    async def rm(self, path):
        return await self.exec('rm', self.path(path))

    async def getenv(self, key):
        return (await self.exec('echo $' + key)).out

    async def getcwd(self):
        return (await self.exec('pwd')).out
