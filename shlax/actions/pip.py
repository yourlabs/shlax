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
        super().__init__(*pip_packages, pip=pip, requirements=requirements)

    async def call(self, *args, **kwargs):
        self.pip = await self.which('pip3', 'pip', 'pip2')
        if not self.pip:
            from .packages import Packages
            action = self.action(Packages, 'python3,apk', 'python3-pip,apt', args=args, kwargs=kwargs)
            await action(*args, **kwargs)

        self.pip = await self.which('pip3', 'pip', 'pip2')
        if not self.pip:
            raise Exception('Could not install a pip command')

        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), 'pip')
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', 'pip')

        if getattr(self, 'mount', None):
            # we are in a target which shares a mount command
            await self.mount(cache, '/root/.cache/pip')
        await self.exec(f'{self.pip} install --upgrade pip')

        # https://github.com/pypa/pip/issues/5599
        self.pip = 'python3 -m pip'

        source = [p for p in self.pip_packages if p.startswith('/')]
        if source:
            await self.exec(
                f'{self.pip} install --upgrade --editable {" ".join(source)}'
            )

        nonsource = [p for p in self.pip_packages if not p.startswith('/')]
        if nonsource:
            await self.exec(f'{self.pip} install --upgrade {" ".join(nonsource)}')

        if self.requirements:
            await self.exec(f'{self.pip} install --upgrade -r {self.requirements}')
