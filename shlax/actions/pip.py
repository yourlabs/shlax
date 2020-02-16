from glob import glob
import os

from .base import Action


class Pip(Action):
    def __init__(self, *pip_packages, pip=None, requirements=None):
        self.requirements = requirements
        super().__init__(*pip_packages, pip=pip, requirements=requirements)

    async def call(self, *args, **kwargs):
        pip = await self.which('pip3', 'pip', 'pip2')
        if pip:
            pip = pip[0]
        else:
            from .packages import Packages
            action = self.action(
                Packages,
                'python3,apk', 'python3-pip,apt',
                args=args, kwargs=kwargs
            )
            await action(*args, **kwargs)
            pip = await self.which('pip3', 'pip', 'pip2')
            if not pip:
                raise Exception('Could not install a pip command')
            else:
                pip = pip[0]

        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), 'pip')
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', 'pip')

        if getattr(self, 'mount', None):
            # we are in a target which shares a mount command
            await self.mount(cache, '/root/.cache/pip')
        await self.exec(f'{pip} install --upgrade pip')

        # https://github.com/pypa/pip/issues/5599
        pip = 'python3 -m pip'

        source = [p for p in self.args if p.startswith('/') or p.startswith('.')]
        if source:
            await self.exec(
                f'{pip} install --upgrade --editable {" ".join(source)}'
            )

        nonsource = [p for p in self.args if not p.startswith('/')]
        if nonsource:
            await self.exec(f'{pip} install --upgrade {" ".join(nonsource)}')

        if self.requirements:
            await self.exec(f'{pip} install --upgrade -r {self.requirements}')
