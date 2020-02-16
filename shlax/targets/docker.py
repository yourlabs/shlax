import asyncio
from pathlib import Path
import os

from ..image import Image
from .localhost import Localhost


class Docker(Localhost):
    contextualize = Localhost.contextualize + ['mnt', 'ctr', 'mount']

    def __init__(self, *args, **kwargs):
        self.image = kwargs.get('image', 'alpine')
        if not isinstance(self.image, Image):
            self.image = Image(image)
        super().__init__(*args, **kwargs)
        self.context['ctr'] = None

    def shargs(self, *args, daemon=False, **kwargs):
        if args[0] == 'docker':
            return args, kwargs

        extra = []
        if 'user' in kwargs:
            extra += ['--user', kwargs.pop('user')]

        args, kwargs = super().shargs(*args, **kwargs)

        if self.context['ctr']:
            executor = 'exec'
            extra = [self.context['ctr']]
            return [self.kwargs.get('docker', 'docker'), executor, '-t'] + extra + list(args), kwargs

        executor = 'run'
        cwd = os.getcwd()
        if daemon:
            extra += ['-d']
        extra = extra + ['-v', f'{cwd}:{cwd}', '-w', f'{cwd}']
        return [self.kwargs.get('docker', 'docker'), executor, '-t'] + extra + [str(self.image)] + list(args), kwargs

    async def call(self, *args, **kwargs):
        name = kwargs.get('name', os.getcwd()).split('/')[-1]
        self.context['ctr'] = (
            await self.exec(
                'docker', 'ps', '-aq', '--filter',
                'name=' + name,
                raises=False
            )
        ).out.split('\n')[0]

        if 'recreate' in args and self.context['ctr']:
            await self.exec('docker', 'rm', '-f', self.context['ctr'])
            self.context['ctr'] = None

        if self.context['ctr']:
            self.context['ctr'] = (await self.exec('docker', 'start', name)).out
        else:
            self.context['ctr'] = (
                await self.exec('sleep', '120', daemon=True)
            ).out
        return await super().call(*args, **kwargs)

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
            args = ['docker', 'cp', s, self.context['ctr'] + ':' + dst]
            procs.append(self.exec(*args))

        return await asyncio.gather(*procs)
