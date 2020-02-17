import asyncio
from pathlib import Path
import os

from ..image import Image
from .localhost import Localhost


class Docker(Localhost):
    contextualize = Localhost.contextualize + ['mnt', 'ctr', 'mount']

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

        if step('rm'):
            await self.rm(*args, **kwargs)

        if step('down') and self.name:
            await self.exec('docker', 'down', '-f', self.name)

        if step('up'):
            await self.up(*args, **kwargs)
        return await super().call(*args, **kwargs)

    async def rm(self, *args, **kwargs):
        return await self.exec('docker', 'rm', '-f', self.name)

    async def down(self, *args, **kwargs):
        """Remove instance, except persistent data if any"""
        if self.name:
            self.name = (await self.exec('docker', 'start', self.name)).out
        else:
            self.name = (await self.exec('docker', 'run', '-d', '--name', self.name)).out

    async def up(self, *args, **kwargs):
        """Perform start or run"""
        if self.name:
            self.name = (await self.exec('docker', 'start', self.name)).out
        else:
            self.id = (await self.exec('docker', 'run', '-d', '--name', self.name)).out

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
