import os
from .script import Script
from ..image import Image


class Container(Script):
    """
    Wolcome to crazy container control cli

    Such wow
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('start', dict())
        super().__init__(*args, **kwargs)

    async def call(self, *args, **kwargs):
        if step('build'):
            await self.kwargs['build'](**kwargs)
            self.image = self.kwargs['build'].image
        else:
            self.image = kwargs.get('image', 'alpine')
        if isinstance(self.image, str):
            self.image = Image(self.image)

        if step('install'):
            await self.install(*args, **kwargs)

        if step('test'):
            self.output.test(self)
            await self.action('Docker',
                *self.kwargs['test'].actions,
                image=self.image,
                mount={'.': '/app'},
                workdir='/app',
            )(**kwargs)

        if step('push'):
            await self.image.push(action=self)

        #name = kwargs.get('name', os.getcwd()).split('/')[-1]


class Pod(Script):
    pass
