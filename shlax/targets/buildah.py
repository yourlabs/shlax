import os
import sys
from pathlib import Path

from .base import Target

from ..image import Image
from ..proc import Proc


class Buildah(Target):
    def __init__(self,
                 *actions,
                 base=None, commit=None,
                 cmd=None):
        self.base = base or 'alpine'
        self.image = Image(commit) if commit else None

        self.ctr = None
        self.mnt = None
        self.mounts = dict()

        self.config = dict(
            cmd=cmd or 'sh',
        )

        # Always consider localhost as parent for now
        self.parent = Target()

        super().__init__(*actions)

    def is_runnable(self):
        return Proc.test or os.getuid() == 0

    def __str__(self):
        if not self.is_runnable():
            return 'Replacing with: buildah unshare ' + ' '.join(sys.argv)
        return 'Buildah image builder'

    async def __call__(self, *actions, target=None):
        if target:
            self.parent = target

        if not self.is_runnable():
            os.execvp('buildah', ['buildah', 'unshare'] + sys.argv)
            # program has been replaced

        self.ctr = (await self.parent.exec('buildah', 'from', self.base)).out
        self.mnt = Path((await self.parent.exec('buildah', 'mount', self.ctr)).out)
        await super().__call__()

    async def clean(self, target):
        for src, dst in self.mounts.items():
            await self.parent.exec('umount', self.mnt / str(dst)[1:])

        if self.result.status == 'success':
            await self.commit()
            if os.getenv('BUILDAH_PUSH'):
                await self.image.push(target)

        if self.mnt is not None:
            await self.parent.exec('buildah', 'umount', self.ctr)

        if self.ctr is not None:
            await self.parent.exec('buildah', 'rm', self.ctr)

    async def mount(self, src, dst):
        """Mount a host directory into the container."""
        target = self.mnt / str(dst)[1:]
        await self.parent.exec(f'mkdir -p {src} {target}')
        await self.parent.exec(f'mount -o bind {src} {target}')
        self.mounts[src] = dst

    async def exec(self, *args, user=None, **kwargs):
        _args = ['buildah', 'run']
        if user:
            _args += ['--user', user]
        _args += [self.ctr, '--', 'sh', '-euc']
        _args += [' '.join([str(a) for a in args])]
        return await self.parent.exec(*_args, **kwargs)

    async def commit(self):
        if not self.image:
            return

        for key, value in self.config.items():
            await self.parent.exec(f'buildah config --{key} "{value}" {self.ctr}')

        self.sha = (await self.exec(
            'buildah',
            'commit',
            '--format=' + self.image.format,
            self.ctr,
            buildah=False,
        )).out

        if self.image.tags:
            tags = [f'{self.image.repository}:{tag}' for tag in self.image.tags]
        else:
            tags = [self.image.repository]

        for tag in tags:
            await self.parent.exec('buildah', 'tag', self.sha, tag)
