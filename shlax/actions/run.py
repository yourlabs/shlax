from .base import Action


class Run(Action):
    async def __call__(self, *args, **kwargs):
        return (await self.exec(*self.args, **self.kwargs))
