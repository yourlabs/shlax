import asyncio

from .script import Script


class Async(Script):
    async def call(self, *args, **kwargs):
        return asyncio.gather(*[
            procs.append(action(*args, **kwargs))
            for action in self.actions
        ])
