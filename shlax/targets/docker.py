import asyncio
from pathlib import Path
import os

from ..image import Image
from .localhost import Localhost


class Docker(Localhost):
    """Manage a docker container."""
    default_steps = ['install', 'up']
    contextualize = ['image', 'home']

    def __init__(self, *args, **kwargs):
        self.image = kwargs.get('image', 'alpine')
        self.name = kwargs.get('name', os.getcwd().split('/')[-1])

        if not isinstance(self.image, Image):
            self.image = Image(self.image)

        super().__init__(*args, **kwargs)

    def shargs(self, *args, daemon=False, **kwargs):
        if args[0] == 'docker':
            return args, kwargs

        extra = []
        if 'user' in kwargs:
            extra += ['--user', kwargs.pop('user')]

        args, kwargs = super().shargs(*args, **kwargs)

        if self.name:
            executor = 'exec'
            extra = [self.name]
            return [self.kwargs.get('docker', 'docker'), executor, '-t'] + extra + list(args), kwargs

        executor = 'run'
        cwd = os.getcwd()
        if daemon:
            extra += ['-d']
        extra = extra + ['-v', f'{cwd}:{cwd}', '-w', f'{cwd}']
        return [self.kwargs.get('docker', 'docker'), executor, '-t'] + extra + [str(self.image)] + list(args), kwargs

    async def call(self, *args, **kwargs):
        def step(step):
            return not args or step in args

        # self.name = (
        #     await self.exec(
        #         'docker', 'ps', '-aq', '--filter',
        #         'name=' + self.name,
        #         raises=False
        #     )
        # ).out.split('\n')[0]
        if step('install') and 'install' in self.kwargs:
            await self.action(self.kwargs['install'], *args, **kwargs)

        if step('rm') and await self.exists():
            await self.exec('docker', 'rm', '-f', self.name)

        if step('up'):
            if await self.exists():
                self.name = (await self.exec('docker', 'start', self.name)).out
            else:
                self.id = (await self.exec(
                    'docker', 'run', '-d', '--name', self.name, str(self.image))
                ).out
        return await super().call(*args, **kwargs)

    async def exists(self):
        proc = await self.exec(
            'docker', 'ps', '-aq', '--filter',
            'name=' + self.name,
            raises=False
        )
        return bool(proc.out.strip())

    async def copy(self, *args):
        src = args[:-1]
        dst = args[-1]
        await self.mkdir(dst)

        procs = []
        for s in src:
            '''
            if Path(s).is_dir():
                await self.mkdir(s)
                args = ['docker', 'copy', self.ctr, s, Path(dst) / s]
            else:
                args = ['docker', 'copy', self.ctr, s, dst]
            '''
            args = ['docker', 'cp', s, self.name + ':' + dst]
            procs.append(self.exec(*args))

        return await asyncio.gather(*procs)

    async def up(self):
        """Ensure container is up and running."""
        if await self.exists():
            self.name = (await self.exec('docker', 'start', self.name)).out
        else:
            self.id = (await self.exec(
                'docker', 'run', '-d', '--name', self.name, str(self.image))
            ).out
    up.shlaxstep = True

    async def rm(self):
        """Remove container."""
        await self.exec('docker', 'rm', '-f', self.name)
    rm.shlaxstep = True
