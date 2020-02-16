import asyncio
import os
import asyncio
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import textwrap

from ..actions.base import Action
from ..exceptions import Mistake
from ..proc import Proc
from ..image import Image
from .localhost import Localhost


class Buildah(Localhost):
    """
    The build script iterates over visitors and runs the build functions, it
    also provides wrappers around the buildah command.
    """
    contextualize = Localhost.contextualize + ['mnt', 'ctr', 'mount', 'image']

    def __init__(self, base, *args, commit=None, push=False, cmd=None, **kwargs):
        if isinstance(base, Action):
            args = [base] + list(args)
            base = 'alpine'  # default selection in case of mistake
        super().__init__(*args, **kwargs)
        self.base = base
        self.mounts = dict()
        self.ctr = None
        self.mnt = None
        self.image = Image(commit) if commit else None
        self.config= dict(
            cmd=cmd or 'sh',
        )

    def shargs(self, *args, user=None, buildah=True, **kwargs):
        if not buildah or args[0].startswith('buildah'):
            return super().shargs(*args, user=user, **kwargs)

        _args = ['buildah', 'run']
        if user:
            _args += ['--user', user]
        _args += [self.ctr, '--', 'sh', '-euc']
        return super().shargs(
            *(
                _args
                + [' '.join([str(a) for a in args])]
            ),
            **kwargs
        )

    def __repr__(self):
        return f'Base({self.base})'

    async def __call__(self, *args, **kwargs):
        result = await super().__call__(*args, **kwargs)
        return result

    async def config(self, line):
        """Run buildah config."""
        return await self.exec(f'buildah config {line} {self.ctr}', buildah=False)

    async def copy(self, *args):
        """Run buildah copy to copy a file from host into container."""
        src = args[:-1]
        dst = args[-1]
        await self.mkdir(dst)

        procs = []
        for s in src:
            if Path(s).is_dir():
                target = self.mnt / s
                if not target.exists():
                    await self.mkdir(target)
                args = ['buildah', 'copy', self.ctr, s, Path(dst) / s]
            else:
                args = ['buildah', 'copy', self.ctr, s, dst]
            procs.append(self.exec(*args, buildah=False))

        return await asyncio.gather(*procs)

    async def mount(self, src, dst):
        """Mount a host directory into the container."""
        target = self.mnt / str(dst)[1:]
        await self.exec(f'mkdir -p {src} {target}', buildah=False)
        await self.exec(f'mount -o bind {src} {target}', buildah=False)
        self.mounts[src] = dst

    def is_runnable(self):
        return (
            Proc.test
            or os.getuid() == 0
        )

    async def call(self, *args, **kwargs):
        if self.is_runnable():
            self.ctr = (await self.exec('buildah', 'from', self.base, buildah=False)).out
            self.mnt = Path((await self.exec('buildah', 'mount', self.ctr, buildah=False)).out)
            result = await super().call(*args, **kwargs)
            return result

        from shlax.cli import cli
        debug = kwargs.get('debug', False)
        # restart under buildah unshare environment
        argv = [
            'buildah', 'unshare',
            sys.argv[0],  # current script location
            cli.shlaxfile.path,  # current shlaxfile location
        ]
        if debug is True:
            argv.append('-d')
        elif isinstance(debug, str) and debug:
            argv.append('-d=' + debug)
        argv += [
            cli.parser.command.name,  # script name ?
        ]

        await self.exec(*argv)

    async def commit(self):
        if not self.image:
            return

        for key, value in self.config.items():
            await self.exec(f'buildah config --{key} "{value}" {self.ctr}')

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
            await self.exec('buildah', 'tag', self.sha, tag, buildah=False)

    async def push(self):
        user = os.getenv('DOCKER_USER')
        passwd = os.getenv('DOCKER_PASS')
        if user and passwd and os.getenv('CI'):
            self.output.cmd('buildah login -u ... -p ...' + self.image.registry)
            old = self.output.debug
            self.output.debug = False
            await self.exec('buildah', 'login', '-u', user, '-p', passwd, self.image.registry or 'docker.io', )
            self.output.debug = old
        for tag in self.image.tags:
            await self.exec('buildah', 'push', self.image.registry or 'docker.io', f'{self.image.repository}:{tag}')

    async def clean(self, *args, **kwargs):
        if self.is_runnable():
            for src, dst in self.mounts.items():
                await self.exec('umount', self.mnt / str(dst)[1:], buildah=False)

            if self.status == 'success':
                await self.commit()
                if 'push' in args:
                    await self.push()

            if self.mnt is not None:
                await self.exec('buildah', 'umount', self.ctr, buildah=False)

            if self.ctr is not None:
                await self.exec('buildah', 'rm', self.ctr, buildah=False)
