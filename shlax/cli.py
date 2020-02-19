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
import importlib
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
            if not os.path.exists(shlaxfile):
                try:    # missing shlaxfile, what are we gonna do !!
                    mod = importlib.import_module('shlax.repo.' + shlaxfile)
                except ImportError:
                    print('Could not find ' + shlaxfile)
                    self.exit_code = 1
                    return
                shlaxfile = mod.__file__
                self._doc = inspect.getdoc(mod)

            self.shlaxfile = Shlaxfile()
            self.shlaxfile.parse(shlaxfile)
            if 'main' in self.shlaxfile.actions:
                action = self.shlaxfile.actions['main']
                for name, child in self.shlaxfile.actions['main'].menu.items():
                    self[name] = cli2.Callable(
                        name,
                        child.callable(),
                        options={
                            k: cli2.Option(name=k, **v)
                            for k, v in action.options.items()
                        },
                        color=getattr(action, 'color', cli2.YELLOW),
                    )
            for name, action in self.shlaxfile.actions.items():
                self[name] = cli2.Callable(
                    name,
                    action.callable(),
                    options={
                        k: cli2.Option(name=k, **v)
                        for k, v in action.options.items()
                    },
                    color=getattr(action, 'color', cli2.YELLOW),
                    doc=inspect.getdoc(getattr(action, name, None)) or action._doc,
                )
        else:
            from shlax import repo
            path = repo.__path__._path[0]
            for shlaxfile in glob.glob(os.path.join(path, '*.py')):
                name = shlaxfile.split('/')[-1].split('.')[0]
                mod = importlib.import_module('shlax.repo.' + name)
                self[name] = cli2.Callable(name, mod)

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
