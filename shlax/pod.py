import cli2
import json
import os
import sys

from shlax.targets.base import Target
from shlax.actions.parallel import Parallel
from shlax.proc import Proc

from .podman import Podman


class Pod:
    """Help text"""
    def __init__(self, **containers):
        self.containers = containers
        for name, container in self.containers.items():
            container.pod = self
            container.name = name
        self.name = os.getcwd().split('/')[-1]

    async def _call(self, target, method, *names):
        methods = [
            getattr(container, method)
            for name, container in self.containers.items()
            if not names or name in names
        ]
        await target(Parallel(*methods))

    async def build(self, target, *names):
        """Build container images"""
        if not (Proc.test or os.getuid() == 0):
            os.execvp('buildah', ['buildah', 'unshare'] + sys.argv)
        else:
            await self._call(target, 'build', *names)

    async def down(self, target, *names):
        """Delete container images"""
        await self._call(target, 'down', *names)

    async def start(self, target, *names):
        """Start container images"""
        await self._call(target, 'start', *names)

    async def logs(self, target, *names):
        """Start container images"""
        await self._call(target, 'logs', *names)

    async def ps(self, target):
        """Show containers and volumes"""
        containers = []
        names = []
        for container in await Podman(target).ps('-a'):
            for name in container['Names']:
                if name.startswith(self.name + '-'):
                    container['Name'] = name
                    containers.append(container)
                    names.append(name)

        for name, container in self.containers.items():
            full_name = '-'.join([self.name, container.name])
            if full_name in names:
                continue
            containers.append(dict(
                Name=full_name,
                State='not created',
            ))

        cli2.Table(
            ['Name', 'State'],
            *[
                (container['Name'], container['State'])
                for container in containers
            ]
        ).print()

    def __str__(self):
        return f'Pod({self.name})'
