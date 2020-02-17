import copy
import os

from ..exceptions import WrongResult
from ..actions.base import Action
from ..proc import Proc


class Actions(list):
    def __init__(self, owner, actions):
        self.owner = owner
        super().__init__()
        for action in actions:
            self.append(action)

    def append(self, value):
        action = copy.deepcopy(value)
        action.parent = self.owner
        action.status = 'pending'
        super().append(action)


class Script(Action):
    contextualize = ['shargs', 'exec', 'rexec', 'env', 'which', 'copy']

    def __init__(self, *actions, **kwargs):
        self.home = kwargs.pop('home', os.getcwd())
        super().__init__(**kwargs)
        self.actions = Actions(self, actions)

    async def call(self, *args, **kwargs):
        for action in self.actions:
            result = await action(*args, **kwargs)
            if action.status != 'success':
                break

    def pollute(self, gbls):
        for name, script in self.kwargs.items():
            if not isinstance(script, Script):
                continue
            gbls[name] = script
