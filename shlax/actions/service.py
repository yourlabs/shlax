import asyncio

from .base import Action


class Service(Action):
    def __init__(self, *names, state=None):
        self.state = state or 'started'
        self.names = names
        super().__init__()

    async def call(self, *args, **kwargs):
        return asyncio.gather(*[
            self.exec('systemctl', 'start', name, user='root')
            for name in self.names
        ])
