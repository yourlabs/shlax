import copy
import re

from ..output import Output
from ..proc import Proc
from ..result import Result, Results


class Target:
    def __init__(self, *actions):
        self.actions = actions
        self.results = []
        self.output = Output()
        self.parent = None

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

        for action in actions or self.actions:
            if await self.action(action, reraise=bool(actions)):
                break

    async def action(self, action, reraise=False):
        result = Result(self, action)
        self.output.start(action)
        try:
            await action(target=self)
        except Exception as e:
            self.output.fail(action, e)
            result.status = 'failure'
            result.exception = e
            if reraise:
                # nested call, re-raise
                raise
            else:
                return True
        else:
            self.output.success(action)
            result.status = 'success'
        finally:
            self.caller.results.append(result)

            clean = getattr(action, 'clean', None)
            if clean:
                action.result = result
                self.output.clean(action)
                await clean(self)

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
