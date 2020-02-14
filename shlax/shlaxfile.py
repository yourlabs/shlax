import importlib
import os

from .actions.base import Action


class Shlaxfile:
    def __init__(self, actions=None, tests=None):
        self.actions = actions or {}
        self.tests = tests or {}
        self.paths = []

    def parse(self, path):
        spec = importlib.util.spec_from_file_location('shlaxfile', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name, value in mod.__dict__.items():
            if isinstance(value, Action):
                value.name = name
                self.actions[name] = value
            elif callable(value) and getattr(value, '__name__', '').startswith('test_'):
                self.tests[value.__name__] = value
        self.paths.append(path)

    @property
    def path(self):
        return self.paths[0]
