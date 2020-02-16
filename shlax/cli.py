'''
shlax is a micro-framework to orchestrate commands.

  shlax yourfile.py: to list actions you have declared.
  shlax yourfile.py <action>: to execute a given action
  #!/usr/bin/env shlax: when making yourfile.py an executable.
'''

import asyncio
import cli2
import copy
import inspect
import glob
import os
import sys

from .exceptions import *
from .shlaxfile import Shlaxfile
from .targets import Localhost


class ConsoleScript(cli2.ConsoleScript):
    def __call__(self, *args, **kwargs):
        self.shlaxfile = None
        shlaxfile = sys.argv.pop(1) if len(sys.argv) > 1 else ''
        if shlaxfile:
            if os.path.exists(shlaxfile):
                self.shlaxfile = Shlaxfile()
                self.shlaxfile.parse(shlaxfile)
                for name, action in self.shlaxfile.actions.items():
                    self[name] = cli2.Callable(
                        name,
                        action.callable(),
                        options={
                            k: cli2.Option(name=k, **v)
                            for k, v in action.options.items()
                        },
                        color=getattr(action, 'color', cli2.YELLOW),
                    )
            else:
                try:
                    mod = importlib.import_module('shlax.repo.' + shlaxfile)
                except ImportError:
                    print('Could not find ' + shlaxfile)
                    self.exit_code = 1
                    return
        else:
            from shlax import repo
            path = repo.__path__._path[0]
            for shlaxfile in glob.glob(os.path.join(path, '*.py')):
                name = shlaxfile.split('/')[-1].split('.')[0]
                import importlib
                mod = importlib.import_module('shlax.repo.' + name)
                for k, v in mod.__dict__.items():
                    if callable(v):
                        break
                self[name] = cli2.Callable(name, v, doc='lol')

        return super().__call__(*args, **kwargs)

    def call(self, command):
        kwargs = copy.copy(self.parser.funckwargs)
        kwargs.update(self.parser.options)
        try:
            return command(*self.parser.funcargs, **kwargs)
        except WrongResult as e:
            print(e)
            self.exit_code = e.proc.rc
        except ShlaxException as e:
            print(e)
            self.exit_code = 1


cli = ConsoleScript(__doc__).add_module('shlax.cli')
