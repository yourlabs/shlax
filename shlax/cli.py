"""
Shlax executes mostly in 3 ways:
- Execute actions on targets with the command line
- With your shlaxfile as first argument: offer defined Actions
- With the name of a module in shlax.repo: a community maintained shlaxfile
"""
import ast
import cli2
import glob
import inspect
import importlib
import os
import sys


class ConsoleScript(cli2.ConsoleScript):
    def __call__(self):
        repo = os.path.join(os.path.dirname(__file__), 'repo')

        if len(self.argv) > 1:
            repofile = os.path.join(repo, sys.argv[1] + '.py')
            if os.path.isfile(self.argv[1]):
                self.argv = sys.argv[1:]
                self.load_shlaxfile(sys.argv[1])
            elif os.path.isfile(repofile):
                self.argv = sys.argv[1:]
                self.load_shlaxfile(repofile)
            else:
                raise Exception('File not found ' + sys.argv[1])
        else:
            available = glob.glob(os.path.join(repo, '*.py'))
        return super().__call__()


    def load_shlaxfile(self, path):
        with open(path) as f:
            src = f.read()
        tree = ast.parse(src)

        members = []
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            members.append(node.targets[0].id)

        spec = importlib.util.spec_from_file_location('shlaxfile', sys.argv[1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for member in members:
            from shlax.targets.localhost import Localhost
            self[member] = cli2.Callable(member, Localhost(getattr(mod, member)))

cli = ConsoleScript(__doc__)
