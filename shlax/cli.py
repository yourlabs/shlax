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


class Group(cli2.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmdclass = Command


class Command(cli2.Command):
    def call(self, *args, **kwargs):
        return self.shlax_target(self.target)

    def __call__(self, *argv):
        from shlax.targets.base import Target
        self.shlax_target = Target()
        result = super().__call__(*argv)
        self.shlax_target.output.results(self.shlax_target)
        return result


class ActionCommand(Command):
    def call(self, *args, **kwargs):
        self.target = self.target(*args, **kwargs)
        return super().call(*args, **kwargs)


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
