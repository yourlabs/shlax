from glob import glob
import os

from .base import Action


class Pip(Action):
    packages = dict(
        apt=['python3-pip'],
    )

    def __init__(self, *pip_packages, pip=None, requirements=None):
        self.pip_packages = pip_packages
        self.requirements = requirements

    async def call(self, *args, **kwargs):
        breakpoint()
        self.pip = await self.which(('pip3', 'pip', 'pip2'))
        if not self.pip:
            raise Exception('Could not find pip command')

        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), 'pip')
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', 'pip')

        await script.mount(cache, '/root/.cache/pip')
        await script.crexec(f'{self.pip} install --upgrade pip')

        # https://github.com/pypa/pip/issues/5599
        self.pip = 'python3 -m pip'

        pip_packages = []
        for visitor in script.container.visitors:
            pp = getattr(visitor, 'pip_packages', None)
            if not pp:
                continue
            pip_packages += pip_packages

        source = [p for p in pip_packages if p.startswith('/')]
        if source:
            await script.crexec(
                f'{self.pip} install --upgrade --editable {" ".join(source)}'
            )

        nonsource = [p for p in pip_packages if not p.startswith('/')]
        if nonsource:
            await script.crexec(f'{self.pip} install --upgrade {" ".join(nonsource)}')

        if self.requirements:
            await script.crexec(f'{self.pip} install --upgrade -r {self.requirements}')
