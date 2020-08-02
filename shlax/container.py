import copy
import os

from .image import Image


class Container:
    def __init__(self, build=None, image=None, env=None, volumes=None):
        self.build = build
        self.image = image or self.build.image
        if isinstance(self.image, str):
            self.image = Image(self.image)
        self.volumes = volumes or {}
        self.env = env or {}
        prefix = os.getcwd().split('/')[-1]
        repo = self.image.repository.replace('/', '-')
        if prefix == repo:
            self.name = repo
        else:
            self.name = '-'.join([prefix, repo])

    async def up(self, target, *args):
        """Start the container foreground"""
        cmd = [
            'podman',
            'run',
        ] + list(args)

        for src, dest in self.volumes.items():
            cmd += ['--volume', ':'.join([src, dest])]

        for src, dest in self.env.items():
            cmd += ['--env', '='.join([src, str(dest)])]

        cmd += [
            '--name',
            self.name,
            str(self.image),
        ]
        await target.exec(*cmd)

    async def start(self, target):
        """Start the container background"""
        await self.up(target, '-d')

    async def stop(self, target):
        """Start the container"""
        await target.exec('podman', 'stop', self.name)

    async def down(self, target):
        """Start the container"""
        await target.exec('podman', 'rm', '-f', self.name, raises=False)

    async def apply(self, target):
        """Start the container"""
        if self.build:
            await target(self.build)
        await target(self.down)
        await target(self.start)

    def __str__(self):
        return f'Container(name={self.name}, image={self.image}, volumes={self.volumes})'
