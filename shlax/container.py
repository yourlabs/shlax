import os

from .image import Image


class Container:
    def __init__(self, build=None, image=None):
        self.build = build
        self.image = self.build.image
        prefix = os.getcwd().split('/')[-1]
        repo = self.image.repository.replace('/', '-')
        if prefix == repo:
            self.name = repo
        else:
            self.name = '-'.join([prefix, repo])

    async def start(self, target):
        """Start the container"""
        await target.rexec(
            'podman',
            'run',
            '--name',
            self.name,
            str(self.image),
        )

    async def stop(self, target):
        """Start the container"""
        await target.rexec('podman', 'stop', self.name)

    def __str__(self):
        return f'Container(name={self.name}, image={self.image})'
