import os
import re

class Image:
    ENV_TAGS = (
        # gitlab
        'CI_COMMIT_SHORT_SHA',
        'CI_COMMIT_REF_NAME',
        'CI_COMMIT_TAG',
        # CircleCI
        'CIRCLE_SHA1',
        'CIRCLE_TAG',
        'CIRCLE_BRANCH',
        # contributions welcome here
    )

    PATTERN = re.compile(
        '^((?P<backend>[a-z]*)://)?((?P<registry>[^/]*[.][^/]*)/)?((?P<repository>[^:]+))?(:(?P<tags>.*))?$'  # noqa
        , re.I
    )

    def __init__(self, arg=None, format=None, backend=None, registry=None, repository=None, tags=None):
        self.arg = arg
        self.format = format
        self.backend = backend
        self.registry = registry
        self.repository = repository
        self.tags = tags or []

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
        self.format = format or 'oci'
        if self.registry == 'docker.io':
            self.format = 'docker'

        # figure tags from CI vars
        for name in self.ENV_TAGS:
            value = os.getenv(name)
            if value:
                self.tags.append(value)

        # filter out tags which resolved to None
        self.tags = [t for t in self.tags if t]

        # default tag by default ...
        if not self.tags:
            self.tags = ['latest']

    async def __call__(self, action, *args, **kwargs):
        args = list(args)
        return await action.exec(*args, **self.kwargs)

    def __str__(self):
        return self.repository
