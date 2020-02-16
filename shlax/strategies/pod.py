import os
from .script import Script


class Container(Script):
    async def call(self, *args, **kwargs):
        if not args or 'build' in args:
            await self.kwargs['build'](*args, **kwargs)
        self.image = self.kwargs['build'].image

        if not args or 'test' in args:
            self.output.test(self)
            await self.action('Docker',
                *self.kwargs['test'].actions,
                image=self.image,
                mount={'.': '/app'},
                workdir='/app',
            )(*args, **kwargs)

        if not args or 'push' in args:
            user = os.getenv('DOCKER_USER')
            passwd = os.getenv('DOCKER_PASS')
            if user and passwd and os.getenv('CI') and self.registry:
                await self.exec(
                    'podman',
                    'login',
                    '-u',
                    user,
                    '-p',
                    passwd,
                    self.registry,
                    buildah=False,
                )

            for tag in self.image.tags:
                await self.exec('podman', 'push', f'{self.image.repository}:{tag}')

        #name = kwargs.get('name', os.getcwd()).split('/')[-1]


class Pod(Script):
    pass
