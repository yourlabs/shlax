from .base import Action


class Run(Action):
    async def call(self, *args, **kwargs):
        return (await self.exec(*self.args, **self.kwargs))
