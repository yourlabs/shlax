from .base import Action


class Copy(Action):
    """Copy files or directories to target."""
    async def call(self, *args, **kwargs):
        await self.copy(*self.args)
