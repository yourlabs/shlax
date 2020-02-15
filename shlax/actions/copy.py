from .base import Action


class Copy(Action):
    async def call(self, *args, **kwargs):
        await self.copy(*self.args)
