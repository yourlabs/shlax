import asyncio
import os
import asyncio
from pathlib import Path
import signal
import shlex
import subprocess
import sys
import textwrap

from ..proc import Proc
from ..image import Image
from .localhost import Localhost


class Buildah(Localhost):
    """
    The build script iterates over visitors and runs the build functions, it
    also provides wrappers around the buildah command.
    """
    contextualize = Localhost.contextualize + ['mnt', 'ctr']

    def __init__(self, base, *args, commit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = base
        self.mounts = dict()
        self.ctr = None
        self.mnt = None
        self.commit = commit

    def shargs(self, *args, user=None, buildah=True, **kwargs):
        if not buildah:
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

    async def config(self, line):
        """Run buildah config."""
        return await self.exec(f'buildah config {line} {self.ctr}', buildah=False)

    async def mkdir(self, *dirs):
        return await self.exec(*['mkdir', '-p'] + list(dirs))

    async def copy(self, *args):
        """Run buildah copy to copy a file from host into container."""
        src = args[:-1]
        dst = args[-1]
        await self.mkdir(dst)

        args = ['buildah', 'copy', self.ctr] + list(
            [str(a) for a in src]
        ) + [str(dst)]
        return await self.exec(*args, buildah=False)

    async def mount(self, src, dst):
        """Mount a host directory into the container."""
        target = self.mnt / str(dst)[1:]
        await self.exec(f'mkdir -p {src} {target}')
        await self.exec(f'mount -o bind {src} {target}')
        self.mounts[src] = dst

    async def umounts(self):
        """Unmount all mounted directories from the container."""
        for src, dst in self.mounts.items():
            await super().exec('umount', self.mnt / str(dst)[1:])

    async def umount(self):
        """Unmount the buildah container with buildah unmount."""
        if self.ctr:
            await super().exec(f'buildah unmount {self.ctr}')

    async def which(self, *cmd):
        """
        Return the first path to the cmd in the container.

        If cmd argument is a list then it will try all commands.
        """
        paths = (await self.env('PATH')).split(':')
        for path in paths:
            for c in cmd:
                p = os.path.join(self.mnt, path[1:], c)
                if os.path.exists(p):
                    return p[len(str(self.mnt)):]

    def __repr__(self):
        return f'Build'

    @property
    def _compatible(self):
        return Proc.test or os.getuid() == 0 or getattr(self.parent, 'parent', None)

    async def call(self, *args, **kwargs):
        if self._compatible:
            self.ctr = (await self.exec('buildah', 'from', self.base, buildah=False)).out
            self.mnt = Path((await self.exec('buildah', 'mount', self.ctr, buildah=False)).out)

            return await super().call(*args, **kwargs)

        from shlax.cli import cli
        debug = kwargs.get('debug', False)
        # restart under buildah unshare environment
        argv = [
            'buildah', 'unshare',
            sys.argv[0],  # current script location
        ]
        if debug is True:
            argv.append('-d')
        elif isinstance(debug, str):
            argv.append('-d=' + debug)
        argv += [
            cli.shlaxfile.path,
            cli.parser.command.name,  # script name ?
        ]
        self.output(' '.join(argv), 'EXECUTION', flush=True)

        proc = await asyncio.create_subprocess_shell(
            shlex.join(argv),
            stderr=sys.stderr,
            stdin=sys.stdin,
            stdout=sys.stdout,
        )
        await proc.communicate()
        cli.exit_code = await proc.wait()

    async def clean(self, *args, **kwargs):
        if self.mnt:
            await self.exec('buildah', 'umount', self.ctr, buildah=False)
        if self.ctr:
            await self.exec('buildah', 'rm', self.ctr, buildah=False)
