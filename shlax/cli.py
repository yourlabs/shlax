"""
Shlax automation tool manual

Shlax is built mostly around 3 moving pieces:
- Target: a target host and protocol
- Action: execute a shlax action
- Strategy: defines how to apply actions on targets (scripted only)

Shlax executes mostly in 3 ways:
- Execute actions on targets with the command line
- With your shlaxfile as first argument: offer defined Actions
- With the name of a module in shlax.repo: a community maintained shlaxfile
"""

import copy
import cli2
import inspect
import importlib
import glob
import os
import sys

from .actions.base import Action
from .exceptions import ShlaxException, WrongResult
from .strategies import Script


class ConsoleScript(cli2.ConsoleScript):
    class Parser(cli2.Parser):
        def __init__(self, *args, **kwargs):
            self.targets = dict()
            super().__init__(*args, **kwargs)

        def append(self, arg):
            if '=' not in arg and '@' in arg:
                if '://' in arg:
                    kind, spec = arg.split('://')
                else:
                    kind = 'ssh'
                    spec = arg

                mod = importlib.import_module('shlax.targets.' + kind)
                target = getattr(mod, kind.capitalize())(spec)
                self.targets[str(target)] = target
            else:
                super().append(arg)

    def __call__(self):
        if len(self.argv) > 1 and os.path.exists(self.argv[1]):
            self.argv = sys.argv[1:]

            spec = importlib.util.spec_from_file_location('shlaxfile', sys.argv[1])
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.doc = (inspect.getdoc(mod) or '').split("\n")[0]
            for name, value in mod.__dict__.items():
                if isinstance(value, Action):
                    self[name] = cli2.Callable(
                        name,
                        self.action(value),
                        doc=type(value).__doc__,
                        options={
                            option: cli2.Option(option, **cfg)
                            for option, cfg in value.options.items()
                        }
                    )
                    #self[name] = value
                #elif callable(value) and getattr(value, '__name__', '').startswith('test_'):
                #    self.tests[value.__name__] = value

            #modname = sys.argv[1].split('/')[-1].replace('.py', '')
            #mod = importlib.import_module('shlax.actions.' + modname)
        else:
            scripts = glob.glob(os.path.join(
                os.path.dirname(__file__), 'actions', '*.py'))
            for script in scripts:
                modname = script.split('/')[-1].replace('.py', '')
                if modname == '__init__':
                    continue

                mod = importlib.import_module('shlax.actions.' + modname)
                for key, value in mod.__dict__.items():
                    if key == '__builtins__':
                        continue
                    if key.lower() != modname:
                        continue
                    break
                self[modname] = cli2.Callable(
                    modname,
                    self.action_class(value),
                    options={
                        option: cli2.Option(option, **cfg)
                        for option, cfg in value.options.items()
                    }
                )

            scripts = glob.glob(os.path.join(
                os.path.dirname(__file__), 'repo', '*.py'))
            for script in scripts:
                modname = script.split('/')[-1].replace('.py', '')
                mod = importlib.import_module('shlax.repo.' + modname)
                self[modname] = cli2.Group(key, doc=inspect.getdoc(mod))
                for key, value in mod.__dict__.items():
                    if not isinstance(value, Action):
                        continue
                    doc = (inspect.getdoc(mod) or '').split("\n")[0]
                    if key == 'main':
                        if len(value.steps()) == 1:
                            self[modname] = cli2.Callable(
                                modname,
                                self.action(value),
                                doc=doc,
                                options={
                                    option: cli2.Option(option, **cfg)
                                    for option, cfg in value.options.items()
                                }
                            )
                        else:
                            for name, method in value.steps().items():
                                self[modname][name] = cli2.Callable(
                                    modname,
                                    self.action(value),
                                    doc=inspect.getdoc(method),
                                    options={
                                        option: cli2.Option(option, **cfg)
                                        for option, cfg in value.options.items()
                                    }
                                )
                    else:
                        if len(value.steps()) == 1:
                            self[modname][key] = cli2.Callable(
                                modname,
                                self.action(value),
                                doc=doc,
                                options={
                                    option: cli2.Option(option, **cfg)
                                    for option, cfg in value.options.items()
                                }
                            )
                        else:
                            self[modname][key] = cli2.Group('steps')
                            for step in value.steps():
                                self[modname][key][step] = cli2.Callable(
                                    modname,
                                    self.action(value),
                                    doc='lol',
                                    options={
                                        option: cli2.Option(option, **cfg)
                                        for option, cfg in value.options.items()
                                    }
                                )

        return super().__call__()

    def action(self, action):
        async def cb(*args, **kwargs):
            options = dict(steps=args)
            options.update(self.parser.options)
            # UnboundLocalError: local variable 'action' referenced before assignment
            # ??? gotta be missing something, commenting meanwhile
            # action = copy.deepcopy(action)
            return await action(*self.parser.targets, **options)
        cb.__name__ = type(action).__name__
        return cb

    def action_class(self, action_class):
        async def cb(*args, **kwargs):
            argspec = inspect.getfullargspec(action_class)
            required = argspec.args[1:]
            missing = []
            for i, name in enumerate(required):
                if len(args) - 1 <= i:
                    continue
                if name in kwargs:
                    continue
                missing.append(name)
            if missing:
                if not args:
                    print('No args provided after action name ' + action_class.__name__.lower())
                print('Required arguments: ' + ', '.join(argspec.args[1:]))
                if args:
                    print('Provided: ' + ', '.join(args))
                print('Missing arguments: ' + ', '.join(missing))
                print('Try to just add args on the command line separated with a space')
                print(inspect.getdoc(action_class))
                example = 'Example: shlax action '
                example += action_class.__name__.lower()
                if args:
                    example += ' ' + ' '.join(args)
                example += ' ' + ' '.join(missing)
                print(example)
                return

            _args = []
            steps = []
            for arg in args:
                if arg in action_class.steps():
                    steps.append(arg)
                else:
                    _args.append(arg)

            options = dict(steps=steps)

            '''
            varargs = argspec.varargs
            if varargs:
                extra = args[len(argspec.args) - 1:]
                args = args[:len(argspec.args) - 1]
                options = dict(steps=extra)
            else:
                extra = args[len(argspec.args) - 1:]
                args = args[:len(argspec.args) - 1]
                options = dict(steps=extra)
            '''
            options.update(self.parser.options)
            return await action_class(*_args, **kwargs)(*self.parser.targets, **options)
        cb.__doc__ = (inspect.getdoc(action_class) or '').split("\n")[0]
        cb.__name__ = action_class.__name__
        return cb

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
