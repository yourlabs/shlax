"""
Shlax executes mostly in 3 ways:
- Execute actions on targets with the command line
- With your shlaxfile as first argument: offer defined Actions
- With the name of a module in shlax.repo: a community maintained shlaxfile
"""
import ast
import asyncio
import cli2
import glob
import inspect
import importlib
import os
import sys

from .proc import ProcFailure


class Group(cli2.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmdclass = Command


class TargetArgument(cli2.Argument):
    """
    Target to execute on: localhost by default, target=@ssh_host for ssh.
    """

    def __init__(self, cmd, param, doc=None, color=None, default=None):
        from shlax.targets.base import Target
        super().__init__(cmd, param, doc=self.__doc__, default=Target())
        self.alias = ['target', 't']

    def cast(self, value):
        from shlax.targets.ssh import Ssh
        user, host = value.split('@')
        return Ssh(host=host, user=user)

    def match(self, arg):
        return arg if isinstance(arg, str) and '@' in arg else None


class Command(cli2.Command):
    def setargs(self):
        super().setargs()
        if 'target' in self.sig.parameters:
            self['target'] = TargetArgument(
                self,
                self.sig.parameters['target'],
            )
        if 'actions' in self:
            del self['actions']

    def __call__(self, *argv):
        result = None

        try:
            result = super().__call__(*argv)
        except ProcFailure:
            # just output the failure without TB, as command was already
            # printed anyway
            pass

        if self['target'].value.results:
            if self['target'].value.results[-1].status == 'failure':
                self.exit_code = 1
        self['target'].value.output.results(self['target'].value)
        return result


class ActionCommand(cli2.Command):
    def setargs(self):
        super().setargs()
        self['target'] = TargetArgument(
            self,
            inspect.Parameter('target', inspect.Parameter.KEYWORD_ONLY),
        )

    def call(self, *args, **kwargs):
        self.target = self.target(*args, **kwargs)
        return super().call(self['target'].value)


class ConsoleScript(Group):
    def __call__(self, *argv):
        self.load_actions()
        #self.load_shlaxfiles()  # wip
        return super().__call__(*argv)

    def load_shlaxfiles(self):
        filesdir = os.path.dirname(__file__) + '/shlaxfiles/'
        for filename in os.listdir(filesdir):
            filepath = filesdir + filename
            if not os.path.isfile(filepath):
                continue

            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())
            group = self.group(filename[:-3])

            main = Group(doc=__doc__).load(shlax)

    def load_actions(self):
        actionsdir = os.path.dirname(__file__) + '/actions/'
        for filename in os.listdir(actionsdir):
            filepath = actionsdir + filename
            if not os.path.isfile(filepath):
                continue
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())
            cls = [
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef)
            ]
            if not cls:
                continue
            mod = importlib.import_module('shlax.actions.' + filename[:-3])
            cls = getattr(mod, cls[0].name)
            self.add(cls, name=filename[:-3], cmdclass=ActionCommand)


cli = ConsoleScript(doc=__doc__)
