import copy
import re

from ..output import Output
from ..proc import Proc
from ..result import Result, Results


class Target:
    def __init__(self, *actions, **options):
        self.actions = actions
        self.options = options
        self.results = []
        self.output = Output(self, **self.options)
        self.parent = None

    @property
    def caller(self):
        """Traverse parents and return the top-levels Target."""
        if not self.parent:
            return self
        caller = self.parent
        while caller.parent:
            caller = caller.parent
        return caller

    async def __call__(self, *actions, target=None):
        if target:
            # that's going to be used by other target methods, to access
            # the calling target
            self.parent = target

        for action in actions or self.actions:
            result = Result(self, action)

            self.output = Output(action, **self.options)
            self.output.start()
            try:
                await action(target=self)
            except Exception as e:
                self.output.fail(e)
                result.status = 'failure'
                result.exception = e
                if actions:
                    # nested call, re-raise
                    raise
                else:
                    break
            else:
                self.output.success()
                result.status = 'success'
            finally:
                self.caller.results.append(result)

                clean = getattr(action, 'clean', None)
                if clean:
                    action.result = result
                    self.output.clean()
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

    async def exec(self, *args, **kwargs):
        raise NotImplemented()