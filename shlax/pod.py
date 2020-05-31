import cli2

from shlax.targets.base import Target
from shlax.actions.parallel import Parallel


class Pod:
    """Help text"""
    def __init__(self, **containers):
        self.containers = containers

    async def _call(self, target, method, *names):
        methods = [
            getattr(container, method)
            for name, container in self.containers.items()
            if not names or name in names
        ]
        await target(Parallel(*methods))

    async def build(self, target, *names):
        """Build container images"""
        await self._call(target, 'build', *names)

    async def start(self, target, *names):
        """Start container images"""
        await self._call(target, 'start', *names)
