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
            await self.kwargs['build'](method='push', **kwargs)

        #name = kwargs.get('name', os.getcwd()).split('/')[-1]


class Pod(Script):
    pass
