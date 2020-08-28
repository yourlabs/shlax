import copy
import os

from .podman import Podman
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

        self.pod = None

    @property
    def full_name(self):
        if self.pod:
            return '-'.join([self.pod.name, self.name])
        return self.name

    async def up(self, target, *args):
        """Start the container foreground"""
        podman = Podman(target)
        if self.pod:
            pod = None
            for _ in await podman.pod.ps():
                if _['Name'] == self.pod.name:
                    pod = _
                    break
            if not pod:
                await podman.pod.create('--name', self.pod.name)
            args = list(args) + ['--pod', self.pod.name]

        # skip if already up
        for result in await podman.ps('-a'):
            for name in result['Names']:
                if name == self.full_name:
                    if result['State'] == 'running':
                        target.output.info(f'{self.full_name} already running')
                        return
                    elif result['State'] in ('exited', 'configured'):
                        target.output.info(f'{self.full_name} starting')
                        await target.exec('podman', 'start', self.full_name)
                        return

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
            self.full_name,
            str(self.image),
        ]
        await target.exec(*cmd)

    async def start(self, target):
        """Start the container background"""
        await self.up(target, '-d')

    async def stop(self, target):
        """Start the container"""
        await target.exec('podman', 'stop', self.full_name)

    async def inspect(self, target):
        """Inspect container"""
        await target.exec('podman', 'inspect', self.full_name)

    async def logs(self, target):
        """Show container logs"""
        await target.exec('podman', 'logs', self.full_name)

    async def exec(self, target, cmd=None):
        """Execute a command in the container"""
        cmd = cmd or 'bash'
        if cmd.endswith('sh'):
            import os
            os.execvp(
                '/usr/bin/podman',
                [
                    'podman',
                    'exec',
                    '-it',
                    self.full_name,
                    cmd,
                ]
            )
        result = await target.exec(
            'podman',
            'exec',
            self.full_name,
            cmd,
        )

    async def down(self, target):
        """Start the container"""
        await target.exec('podman', 'rm', '-f', self.full_name, raises=False)

    async def apply(self, target):
        """Start the container"""
        if self.build:
            await target(self.build)
        await target(self.down)
        await target(self.start)

    def __str__(self):
        return f'Container(name={self.name}, image={self.image}, volumes={self.volumes})'
