import asyncio


class Parallel:
    def __init__(self, *actions):
        self.actions = actions

    async def __call__(self, target):
        return await asyncio.gather(*[
            target(action) for action in self.actions
        ])
