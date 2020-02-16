import os
from .script import Script


class Container(Script):
    async def call(self, *args, **kwargs):
        if not args or 'build' in args:
            await self.kwargs['build'](**kwargs)
        self.image = self.kwargs['build'].image

        if not args or 'test' in args:
            self.output.test(self)
            await self.action('Docker',
                *self.kwargs['test'].actions,
                image=self.image,
                mount={'.': '/app'},
                workdir='/app',
            )(**kwargs)

        if not args or 'push' in args:
            await self.image.push(action=self)

        #name = kwargs.get('name', os.getcwd()).split('/')[-1]


class Pod(Script):
    pass
