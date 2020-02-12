import asyncio
import copy
import cli2
import os
import textwrap

from .proc import Proc


class Script:
    options = [
        cli2.Option(
            'debug',
            alias='d',
            color=cli2.GREEN,
            default='visit',
            help='''
            Display debug output. Supports values (combinable): cmd,out,visit
            '''.strip(),
            immediate=True,
        ),
    ]
    unshare = False

    def __init__(self, name=None, doc=None):
        self.name = name or type(self).__name__.lower()
        self.doc = doc or 'Custom script'

    async def exec(self, *args, **kwargs):
        """Execute a command on the host."""
        if getattr(self, 'container', None) and getattr(self.container, 'name', None):
            kwargs.setdefault('prefix', self.container.name)
        proc = await Proc(*args, **kwargs)()
        if kwargs.get('wait', True):
            await proc.wait()
        return proc

    async def __call__(self, visitable, *args, **kwargs):
        from .console_script import console_script
        debug = console_script.options.get('debug', False)

        self.args = args
        for key, value in kwargs.items():
            setattr(self, key, value)

        visitors = visitable.visitors

        results = []
        async def clean():
            for visitor in visitable.visitors:
                if hasattr(visitor, 'clean_' + self.name):
                    method = 'clean_' + self.name
                    result = getattr(visitor, method)(self)
                    if debug is True or 'visit' in str(debug):
                        print(
                            getattr(visitable, 'name', '') + ' | ',
                            '.'.join([type(visitor).__name__, method]),
                            ' '.join(f'{k}={v}' for k, v in visitor.__dict__.items())
                        )
                    if result:
                        await result

        for prefix in ('init_', 'pre_', '', 'post_', 'clean_'):
            method = prefix + self.name
            for visitor in visitable.visitors:
                if not hasattr(visitor, method):
                    continue

                if debug is True or 'visit' in str(debug):
                    print(
                        getattr(visitable, 'name', '') + ' | ',
                        '.'.join([type(visitor).__name__, method]),
                        ' '.join(f'{k}={v}' for k, v in visitor.__dict__.items())
                    )
                result = getattr(visitor, method)(self)
                if result:
                    try:
                        await result
                    except Exception as e:
                        await clean()
                        raise

    async def run(self, *args, **kwargs):
        if self.unshare and os.getuid() != 0:
            import sys
            # restart under buildah unshare environment !
            os.execvp('buildah', ['buildah', 'unshare'] + sys.argv)

        for key, value in kwargs.items():
            setattr(self, key, value)

        if args:
            containers = [c for c in self.pod.containers if c.name in args]
        else:
            containers = self.pod.containers

        procs = [
            copy.deepcopy(self)(
                self.pod,
                *args,
                **kwargs,
            )
        ]
        procs += [
            copy.deepcopy(self)(
                container,
                *args,
                container=container,
                **kwargs,
            )
            for container in containers
        ]
        return await asyncio.gather(*procs)
