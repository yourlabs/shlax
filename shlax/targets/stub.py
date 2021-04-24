from ..proc import Proc

from .base import Target


class ProcStub(Proc):
    async def __call__(self, wait=True):
        return self

    async def communicate(self):
        self.communicated = True
        return self

    async def wait(self):
        return self


class Stub(Target):
    async def exec(self, *args, **kwargs):
        proc = await ProcStub(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc
