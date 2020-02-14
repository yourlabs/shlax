'''
shlax is a micro-framework to orchestrate commands.

  shlax yourfile.py: to list actions you have declared.
  shlax yourfile.py <action>: to execute a given action
  #!/usr/bin/env shlax: when making yourfile.py an executable.
'''

import asyncio
import cli2
import inspect
import os
import sys

from .exceptions import *
from .shlaxfile import Shlaxfile
from .targets import Localhost


async def runall(*args, **kwargs):
    for name, action in cli.shlaxfile.actions.items():
        await Localhost(action)(*args, **kwargs)


@cli2.option('debug', alias='d', help='Display debug output.')
async def test(*args, **kwargs):
    breakpoint()
    """Run podctl test over a bunch of paths."""
    report = []

    for arg in args:
        candidates = [
            os.path.join(os.getcwd(), arg, 'pod.py'),
            os.path.join(os.getcwd(), arg, 'pod_test.py'),
        ]
        for candidate in candidates:
            if not os.path.exists(candidate):
                continue
            podfile = Podfile.factory(candidate)

            # disable push
            for name, container in podfile.containers.items():
                commit = container.visitor('commit')
                if commit:
                    commit.push = False

            output.print(
                '\n\x1b[1;38;5;160;48;5;118m  BUILD START \x1b[0m'
                + ' ' + podfile.path + '\n'
            )

            old_exit_code = console_script.exit_code
            console_script.exit_code = 0
            try:
                await podfile.pod.script('build')()
            except Exception as e:
                report.append(('build ' + candidate, False))
                continue

            if console_script.exit_code != 0:
                report.append(('build ' + candidate, False))
                continue
            console_script.exit_code = old_exit_code

            for name, test in podfile.tests.items():
                name = '::'.join([podfile.path, name])
                output.print(
                    '\n\x1b[1;38;5;160;48;5;118m   TEST START \x1b[0m'
                    + ' ' + name + '\n'
                )

                try:
                    await test(podfile.pod)
                except Exception as e:
                    report.append((name, False))
                    output.print('\x1b[1;38;5;15;48;5;196m    TEST FAIL \x1b[0m' + name)
                else:
                    report.append((name, True))
                    output.print('\x1b[1;38;5;200;48;5;44m TEST SUCCESS \x1b[0m' + name)
                output.print('\n')

    print('\n')

    for name, success in report:
        if success:
            output.print('\n\x1b[1;38;5;200;48;5;44m TEST SUCCESS \x1b[0m' + name)
        else:
            output.print('\n\x1b[1;38;5;15;48;5;196m    TEST FAIL \x1b[0m' + name)

    print('\n')

    success = [*filter(lambda i: i[1], report)]
    failures = [*filter(lambda i: not i[1], report)]

    output.print(
        '\n\x1b[1;38;5;200;48;5;44m TEST TOTAL: \x1b[0m'
        + str(len(report))
    )
    if success:
        output.print(
            '\n\x1b[1;38;5;200;48;5;44m TEST SUCCESS: \x1b[0m'
            + str(len(success))
        )
    if failures:
        output.print(
            '\n\x1b[1;38;5;15;48;5;196m    TEST FAIL: \x1b[0m'
            + str(len(failures))
        )

    if failures:
        console_script.exit_code = 1


class ConsoleScript(cli2.ConsoleScript):
    def __call__(self, *args, **kwargs):
        self.shlaxfile = None
        shlaxfile = sys.argv.pop(1) if len(sys.argv) > 1 else ''
        if os.path.exists(shlaxfile.split('::')[0]):
            self.shlaxfile = Shlaxfile()
            self.shlaxfile.parse(shlaxfile)
            for name, action in self.shlaxfile.actions.items():
                async def cb(*args, **kwargs):
                    return await Localhost(action)(*args, **kwargs)
                self[name] = cli2.Callable(
                    name,
                    cb,
                    color=getattr(action, 'color', cli2.YELLOW),
                )
        return super().__call__(*args, **kwargs)

    def call(self, command):
        args = self.parser.funcargs
        kwargs = self.parser.funckwargs
        breakpoint()
        return command(*args, **kwargs)

    def call(self, command):
        try:
            return super().call(command)
        except WrongResult as e:
            print(e)
            self.exit_code = e.proc.rc
        except ShlaxException as e:
            print(e)
            self.exit_code = 1


cli = ConsoleScript(__doc__).add_module('shlax.cli')
