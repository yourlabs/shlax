from glob import glob
import os
from urllib import request

from .base import Action


class Pip(Action):
    """Pip abstraction layer."""
    def __init__(self, *pip_packages):
        self.pip_packages = pip_packages

    async def __call__(self, target):
        # ensure python presence
        results = await target.which('python3', 'python')
        if results:
            python = results[0]
        else:
            raise Exception('Could not find pip nor python')

        # ensure pip module presence
        result = await target.exec(python, '-m', 'pip', raises=False)
        if result.rc != 0:
            if not os.path.exists('get-pip.py'):
                req = request.urlopen(
                    'https://bootstrap.pypa.io/get-pip.py'
                )
                content = req.read()
                with open('get-pip.py', 'wb+') as f:
                    f.write(content)

            await target.copy('get-pip.py', '.')
            await target.exec(python, 'get-pip.py')

        # choose a cache directory
        if 'CACHE_DIR' in os.environ:
            cache = os.path.join(os.getenv('CACHE_DIR'), 'pip')
        else:
            cache = os.path.join(os.getenv('HOME'), '.cache', 'pip')

        # and mount it
        if getattr(target, 'mount', None):
            # we are in a target which shares a mount command
            await target.mount(cache, '/root/.cache/pip')

        source = []
        nonsource = []
        for package in self.pip_packages:
            if os.path.exists(package):
                source.append(package)
            else:
                nonsource.append(package)

        if nonsource:
            await target.exec(
                python, '-m', 'pip',
                'install', '--upgrade',
                *nonsource
            )

        if source:
            await target.exec(
                python, '-m', 'pip',
                'install', '--upgrade', '--editable',
                *source
            )

    def __str__(self):
        return f'Pip({", ".join(self.pip_packages)})'
