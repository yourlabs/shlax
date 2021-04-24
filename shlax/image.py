import json
import os
import re


class Layers(set):
    def __init__(self, image):
        self.image = image

    async def ls(self, target):
        """Fetch layers from localhost"""
        ret = set()
        results = await target.parent.exec(
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
                    self.add(name)
        return self

    async def rm(self, target, tags=None):
        """Drop layers for this image"""
        if tags is None:
            tags = [layer for layer in await self.ls(target)]
        await target.exec('podman', 'rmi', *tags, raises=False)


class Image:
    PATTERN = re.compile(
        '^((?P<backend>[a-z]*)://)?((?P<registry>[^/]*[.][^/]*)/)?((?P<repository>[^:]+))?(:(?P<tags>.*))?$'  # noqa
        , re.I
    )

    def __init__(self, arg=None, format=None, backend=None, registry=None,
                 repository=None, tags=None):
        self.arg = arg
        self.format = format
        self.backend = backend
        self.registry = registry
        self.repository = repository
        self.tags = tags or []
        self.layers = Layers(self)

        match = re.match(self.PATTERN, arg)
        if match:
            for k, v in match.groupdict().items():
                if getattr(self, k):
                    continue
                if not v:
                    continue
                if k == 'tags':
                    v = v.split(',')
                setattr(self, k, v)

        # docker.io currently has issues with oci format
        if self.registry == 'docker.io':
            self.backend = 'docker'

        if not self.format:
            self.format = 'docker' if self.backend == 'docker' else 'oci'

        # filter out tags which resolved to None
        self.tags = [t for t in self.tags if t]

        # default tag by default ...
        if not self.tags:
            self.tags = ['latest']

    def __str__(self):
        return f'{self.repository}:{self.tags[-1]}'

    async def push(self, target, name=None):
        user = os.getenv('IMAGES_USER', os.getenv('DOCKER_USER'))
        passwd = os.getenv('IMAGES_PASS', os.getenv('DOCKER_PASS'))
        if user and passwd:
            target.output.cmd('buildah login -u ... -p ...' + self.registry)
            await target.parent.exec(
                'buildah', 'login', '-u', user, '-p', passwd,
                self.registry or 'docker.io', debug=False)

        for tag in self.tags:
            await target.parent.exec(
                'buildah',
                'push',
                self.repository + ':final',
                name if isinstance(name, str) else f'{self.registry}/{self.repository}:{tag}'
            )
