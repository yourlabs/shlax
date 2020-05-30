import copy
import json
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

        actions_done = await self.cache_load(*actions)

        if actions:
            actions = actions[len(actions_done):]
        else:
            self.actions = self.actions[len(actions_done):]

        self.ctr = (await self.parent.exec('buildah', 'from', self.base)).out
        self.mnt = Path((await self.parent.exec('buildah', 'mount', self.ctr)).out)
        await super().__call__(*actions)

    async def cache_load(self, *actions):
        actions_done = []
        result = await self.parent.exec(
            'podman image list --format json',
            quiet=True,
        )
        result = json.loads(result.out)
        images = [item for sublist in result for item in sublist['History']]
        self.hash_previous = None
        for action in actions or self.actions:
            hasher = getattr(action, 'layerhasher', None)
            if not hasher:
                break
            layerhash = hasher(self.hash_previous)
            layerimage = copy.deepcopy(self.image)
            layerimage.tags = [layerhash]
            if 'localhost/' + str(layerimage) in images:
                self.base = str(layerimage)
                self.hash_previous = layerhash
                actions_done.append(action)
                self.output.success(f'Found cached layer for {action}')

        return actions_done

    async def action(self, action, reraise=False):
        result = await super().action(action, reraise)
        hasher = getattr(action, 'layerhasher', None)
        if hasher:
            layerhash = hasher(self.hash_previous if self.hash_previous else None)
            layerimage = copy.deepcopy(self.image)
            layerimage.tags = [layerhash]
            await self.commit(layerimage)
        return result

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
