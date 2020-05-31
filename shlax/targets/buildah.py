import asyncio
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

from .base import Target

from ..image import Image
from ..proc import Proc


class Buildah(Target):
    """Build container image with buildah"""

    def __init__(self,
                 *actions,
                 base=None, commit=None,
                 cmd=None):
        self.base = base or 'alpine'
        self.image = Image(commit) if commit else None

        self.ctr = None
        self.root = None
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
        return f'Buildah({self.image})'

    async def __call__(self, *actions, target=None):
        if target:
            self.parent = target

        if not self.is_runnable():
            os.execvp('buildah', ['buildah', 'unshare'] + sys.argv)
            # program has been replaced

        layers = await self.layers()
        keep = await self.cache_setup(layers, *actions)
        keepnames = [*map(lambda x: 'localhost/' + str(x), keep)]
        self.invalidate = [name for name in layers if name not in keepnames]
        if self.invalidate:
            self.output.info('Invalidating old layers')
            await self.parent.exec(
                'buildah', 'rmi', *self.invalidate, raises=False)

        if actions:
            actions = actions[len(keep):]
            if not actions:
                return self.uptodate()
        else:
            self.actions = self.actions[len(keep):]
            if not self.actions:
                return self.uptodate()

        self.ctr = (await self.parent.exec('buildah', 'from', self.base)).out
        self.root = Path((await self.parent.exec('buildah', 'mount', self.ctr)).out)

        return await super().__call__(*actions)

    def uptodate(self):
        self.clean = None
        self.output.success('Image up to date')
        return

    async def layers(self):
        ret = set()
        results = await self.parent.exec(
            'buildah images --json',
            quiet=True,
        )
        results = json.loads(results.out)

        prefix = 'localhost/' + self.image.repository + ':layer-'
        for result in results:
            if not result.get('names', None):
                continue
            for name in result['names']:
                if name.startswith(prefix):
                    ret.add(name)
        return ret

    async def cache_setup(self, layers, *actions):
        keep = []
        self.image_previous = Image(self.base)
        for action in actions or self.actions:
            action_image = await self.action_image(action)
            name = 'localhost/' + str(action_image)
            if name in layers:
                self.base = self.image_previous = action_image
                keep.append(action_image)
                self.output.skip(f'Found valid cached layer for {action}')
            else:
                break
        return keep

    async def action_image(self, action):
        if self.image_previous:
            prefix = self.image_previous.tags[0]
        else:
            prefix = self.base
        if hasattr(action, 'cachekey'):
            action_key = action.cachekey()
            if asyncio.iscoroutine(action_key):
                action_key = str(await action_key)
        else:
            action_key = str(action)
        key = prefix + action_key
        sha1 = hashlib.sha1(key.encode('ascii'))
        return self.image.layer(sha1.hexdigest())

    async def action(self, action, reraise=False):
        stop = await super().action(action, reraise)
        if not stop:
            action_image = await self.action_image(action)
            await self.parent.exec(
                'buildah',
                'commit',
                '--format=' + action_image.format,
                self.ctr,
                action_image,
            )
            self.image_previous = action_image
        return stop

    async def clean(self, target, result):
        for src, dst in self.mounts.items():
            await self.parent.exec('umount', self.root / str(dst)[1:])

        if self.root is not None:
            await self.parent.exec('buildah', 'umount', self.ctr)

        if self.ctr is not None:
            if result.status == 'success':
                await self.commit()

            await self.parent.exec('buildah', 'rm', self.ctr)

            if result.status == 'success' and os.getenv('BUILDAH_PUSH'):
                await self.image.push(target)

    async def mount(self, src, dst):
        """Mount a host directory into the container."""
        target = self.root / str(dst)[1:]
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

    async def commit(self, image=None):
        image = image or self.image
        if not image:
            return

        if not image:
            # don't go through that if layer commit
            for key, value in self.config.items():
                await self.parent.exec(f'buildah config --{key} "{value}" {self.ctr}')

        self.sha = (await self.parent.exec(
            'buildah',
            'commit',
            '--format=' + image.format,
            self.ctr,
        )).out

        if image.tags:
            tags = [f'{image.repository}:{tag}' for tag in image.tags]
        else:
            tags = [image.repository]

        for tag in tags:
            await self.parent.exec('buildah', 'tag', self.sha, tag)

    async def mkdir(self, path):
        return await self.parent.mkdir(self.path(path))

    async def copy(self, *args):
        return await self.parent.copy(*args[:-1], self.path(args[-1]))
