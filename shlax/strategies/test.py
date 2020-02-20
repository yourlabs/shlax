from .script import Script

class Test(Script):
    async def call(self, *args, backend=None, **kwargs):
        backend = backend or 'Docker'
        breakpoint()
        return await self.action(backend, self.actions, **kwargs)
